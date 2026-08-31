import asyncio
from enum import Enum
from typing import Self

from beartype import beartype
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn


class ProgressEventType(Enum):
    TASK_START = "TASK_START"
    TASK_TIER_ESCALATE = "TASK_TIER_ESCALATE"
    TASK_COMPLETE = "TASK_COMPLETE"
    SCAN_FINISH = "SCAN_FINISH"


@beartype
class ProgressEvent:
    def __init__(
        self: Self, event_type: ProgressEventType, provider: str, message: str, tier_level: int = 1
    ) -> None:
        self.event_type: ProgressEventType = event_type
        self.provider: str = provider
        self.message: str = message
        self.tier_level: int = tier_level


@beartype
class AsyncProgressManager:
    def __init__(self: Self, console: Console, total_targets: int) -> None:
        self.console: Console = console
        self.total_targets: int = total_targets

        self.progress: Progress = Progress(
            SpinnerColumn(),
            TextColumn(text="[bold blue]{task.description}"),
            BarColumn(),
            TextColumn(text="[progress.percentage]{task.percentage:>3.0f}%"),
        )

        self.main_task_id: TaskID = self.progress.add_task(
            description="Scanning Target Vectors...", total=float(total_targets)
        )
        self.active_tasks: dict[str, TaskID] = {}

    @beartype
    async def listen_events(self: Self, event_queue: asyncio.Queue[ProgressEvent]) -> None:
        with Live(
            renderable=Panel(
                renderable=self.progress, title="OSINT Nexus Core Pipeline", border_style="magenta"
            ),
            console=self.console,
            refresh_per_second=10,
        ):
            while True:
                event: ProgressEvent = await event_queue.get()

                if event.event_type == ProgressEventType.TASK_START:
                    task_id: TaskID = self.progress.add_task(
                        description=f"[{event.provider}] {event.message}", total=100.0
                    )
                    self.active_tasks[event.provider] = task_id

                elif event.event_type == ProgressEventType.TASK_TIER_ESCALATE:
                    if event.provider in self.active_tasks:
                        tid: TaskID = self.active_tasks[event.provider]
                        new_desc: str = f"[{event.provider}] Tier {event.tier_level}: {event.message}"
                        self.progress.update(task_id=tid, description=new_desc)

                elif event.event_type == ProgressEventType.TASK_COMPLETE:
                    if event.provider in self.active_tasks:
                        tid_done: TaskID = self.active_tasks.pop(event.provider)
                        self.progress.update(task_id=tid_done, completed=100.0, visible=False)
                        self.progress.advance(task_id=self.main_task_id, advance=1.0)

                elif event.event_type == ProgressEventType.SCAN_FINISH:
                    self.progress.update(task_id=self.main_task_id, completed=float(self.total_targets))
                    event_queue.task_done()
                    break

                event_queue.task_done()

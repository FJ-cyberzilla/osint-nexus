from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar, overload

T = TypeVar("T")


@dataclass
class JSONDict(Mapping[str, T]):
    data: dict[str, T]

    def __getitem__(self, key: str) -> T:
        return self.data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)


@dataclass
class JSONListContainer(Sequence[T]):
    data: list[T]

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[T]: ...

    def __getitem__(self, index: int | slice) -> T | Sequence[T]:
        if isinstance(index, slice):
            return JSONListContainer(data=self.data[index])
        return self.data[index]

    def __len__(self) -> int:
        return len(self.data)


def test_mapping(data: Mapping[str, int]) -> None:
    print(data["a"])


def test_sequence(data: Sequence[int]) -> None:
    print(data[0])


d = JSONDict(data={"a": 1})
test_mapping(d)

l_data = JSONListContainer(data=[1, 2])
test_sequence(l_data)

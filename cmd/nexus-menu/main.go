package main

import (
	"fmt"
	"os"
	"os/exec"

	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	docStyle         = lipgloss.NewStyle().Margin(1, 2)
	titleStyle       = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#A855F7"))
	itemStyle        = lipgloss.NewStyle().PaddingLeft(4)
	selectedItemStyle = lipgloss.NewStyle().PaddingLeft(2).Foreground(lipgloss.Color("#38BDF8"))
)

type item struct {
	title, desc string
}

func (i item) Title() string       { return i.title }
func (i item) Description() string { return i.desc }
func (i item) FilterValue() string { return i.title }

type model struct {
	list list.Model
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "enter":
			selected, ok := m.list.SelectedItem().(item)
			if ok {
				return m, execTarget(selected.title)
			}
		}
	case tea.WindowSizeMsg:
		m.list.SetSize(msg.Width, msg.Height)
	}

	var cmd tea.Cmd
	m.list, cmd = m.list.Update(msg)
	return m, cmd
}

func (m model) View() string {
	return docStyle.Render(m.list.View())
}

func execTarget(target string) tea.Cmd {
	return func() tea.Msg {
		// Validate target against allowlist
		allowedTargets := map[string]bool{
			"build":      true,
			"lint":       true,
			"test":       true,
			"bench":      true,
			"complexity": true,
			"diagnosis":  true,
			"about":      true,
			"clean":      true,
		}

		if !allowedTargets[target] {
			return tea.Quit
		}

		// #nosec G204 -- The target is strictly validated against a whitelist of allowed make targets.
		cmd := exec.Command("make", target)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		cmd.Stdin = os.Stdin
		err := cmd.Run()
		if err != nil {
			return tea.Quit
		}
		return nil
	}
}

func main() {
	items := []list.Item{
		item{title: "all", desc: "Execute primary build and validation suite"},
		item{title: "build", desc: "Build engine binaries with embedded build metadata"},
		item{title: "lint", desc: "Run static code analysis and quality checks"},
		item{title: "test", desc: "Run unit test suite with coverage reporting"},
		item{title: "bench", desc: "Run performance benchmarks"},
		item{title: "complexity", desc: "Analyze code complexity metrics using gocyclo"},
		item{title: "diagnosis", desc: "Execute runtime diagnostics and environment checks"},
		item{title: "clean", desc: "Purge binary artifacts, logs, build output, and module caches"},
	}

	l := list.New(items, list.NewDefaultDelegate(), 0, 0)
	l.Title = "OSINT-Nexus Command Center"
	l.Styles.Title = titleStyle

	m := model{list: l}

	if _, err := tea.NewProgram(m, tea.WithAltScreen()).Run(); err != nil {
		fmt.Println("Error running program:", err)
		os.Exit(1)
	}
}

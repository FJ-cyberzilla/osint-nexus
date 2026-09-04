package ui

import (
	"fmt"

	"github.com/charmbracelet/bubbles/progress"
	"github.com/charmbracelet/bubbles/spinner"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("205")).
			Padding(0, 1)

	moduleStyle = lipgloss.NewStyle().
			PaddingLeft(2)
)

// Model represents the TUI state.
type Model struct {
	progress progress.Model
	spinner  spinner.Model
	status   string
	modules  map[string]float64 // moduleName -> progress (0.0 - 1.0)
	paths    [][]string         // discovered paths
}

// NewModel creates the initial TUI state.
func NewModel() Model {
	p := progress.New(progress.WithDefaultGradient())
	s := spinner.New()
	s.Spinner = spinner.Dot
	return Model{
		progress: p,
		spinner:  s,
		status:   "Starting OSINT-Nexus...",
		modules:  make(map[string]float64),
		paths:    make([][]string, 0),
	}
}

// Init initializes the TUI.
func (m Model) Init() tea.Cmd {
	return tea.Batch(m.spinner.Tick)
}

// Update handles messages.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		if msg.String() == "q" || msg.String() == "ctrl+c" {
			return m, tea.Quit
		}
	case spinner.TickMsg:
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		return m, cmd
	}
	return m, nil
}

// View renders the TUI.
func (m Model) View() string {
	var body []string
	body = append(body, titleStyle.Render("OSINT-Nexus Dashboard"))
	body = append(body, fmt.Sprintf("%s %s", m.spinner.View(), m.status))

	for name, p := range m.modules {
		body = append(body, moduleStyle.Render(fmt.Sprintf("%s: %s", name, m.progress.ViewAs(p))))
	}

	if len(m.paths) > 0 {
		body = append(body, titleStyle.Render("Discovered Paths:"))
		for _, path := range m.paths {
			body = append(body, fmt.Sprintf("  %v", path))
		}
	}

	return lipgloss.JoinVertical(lipgloss.Left, body...) + "\n"
}

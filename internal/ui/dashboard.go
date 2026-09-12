package ui

import (
	"fmt"
	"time"

	"github.com/charmbracelet/bubbles/progress"
	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// UI Theme & Styles
var (
	colorTitle   = lipgloss.Color("205")
	colorFound   = lipgloss.Color("46")  // Green
	colorMissing = lipgloss.Color("218") // Light Pink
	colorUnknown = lipgloss.Color("226") // Yellow (Critical)
	colorInfo    = lipgloss.Color("39")  // Light Blue (Advisory)
	colorBrand   = lipgloss.Color("215") // Light Orange (Brand)
	colorBlue    = lipgloss.Color("33")  // Blue
	colorGray    = lipgloss.Color("240")

	styleTitle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colorTitle).
			Padding(0, 1)

	styleFound   = lipgloss.NewStyle().Foreground(colorFound)
	styleMissing = lipgloss.NewStyle().Foreground(colorMissing)
	styleUnknown = lipgloss.NewStyle().Foreground(colorUnknown)
	styleInfo    = lipgloss.NewStyle().Foreground(colorInfo)
	styleGray    = lipgloss.NewStyle().Foreground(colorGray)
	styleBox     = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorTitle).
			Padding(1, 2).
			Margin(1, 0)
	styleBrand = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorBrand).
			Foreground(colorBrand).
			Padding(0, 1).
			Align(lipgloss.Center)
	styleBlue = lipgloss.NewStyle().Foreground(colorBlue).Bold(true)

	// Tab Styles
	activeTabStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder(), true).
			BorderForeground(colorBrand).
			Foreground(colorBrand).
			Padding(0, 1)

	inactiveTabStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder(), true).
			BorderForeground(colorGray).
			Foreground(colorGray).
			Padding(0, 1)

	unreadTabStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder(), true).
			BorderForeground(colorUnknown).
			Foreground(colorUnknown).
			Padding(0, 1)

	tabWindowStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder(), false, false, false, false).
			Padding(1, 0)
)

// UI Messages
type StatusMsg string
type ProgressMsg float64
type TelemetryMsg string
type FingerprintMsg string
type DeviceTypeMsg string
type RelationMsg string
type ShadowUserMsg string
type HeatmapMsg string
type EmailMsg string
type SocialMediaMsg string
type GraphMsg struct {
	Nodes []string
	Edges []string
}
type FingerbankFindingsMsg struct {
	DeviceName      string
	Score           int
	Vendor          string
	DeviceType      string
	OperatingSystem string
	Vulnerabilities Vulnerabilities
}
type Vulnerabilities struct {
	CveDevices map[string]interface{}
	CveOs      map[string]interface{}
	Message    string
}
type FingerbankStatusMsg struct {
	Enabled bool
	Usage   int
}
type DNSLeakMsg []DNSLeakResult
type DNSLeakResult struct {
	URL       string
	IsLeaking bool
	Error     string
}
type ErrorMsg string
type AdvisoryMsg string

type tickMsg time.Time

// ResultItem represents a single scan result.
type ResultItem struct {
	Platform string
	Found    bool
	Error    string
}

// Model represents the TUI state.
type Model struct {
	progress      progress.Model
	spinner       spinner.Model
	targetUser    string
	status        string
	results       []ResultItem
	telemetry     string
	fingerprint   string
	deviceType    string
	emails        []string
	socialMedia   []string
	relations     []string
	shadowUsers   []string
	heatmap       string
	graphNodes    []string
	graphEdges    []string
	fingerbank    *FingerbankFindingsMsg
	fbStatus      *FingerbankStatusMsg
	dnsLeaks      []DNSLeakResult
	errors        []string
	advisories    []string
	startTime     time.Time
	percent       float64
	liveStatus    string
	statusPhrases []string
	phraseIdx     int

	// Tab and Viewport state
	viewport  viewport.Model
	ready     bool
	tabs      []string
	activeTab int
	unread    map[string]bool
}

func NewModel(username string) Model {
	p := progress.New(progress.WithDefaultGradient())
	s := spinner.New()
	s.Spinner = spinner.Dot
	return Model{
		progress:    p,
		spinner:     s,
		targetUser:  username,
		status:      "Initializing engine...",
		results:     make([]ResultItem, 0),
		emails:      make([]string, 0),
		socialMedia: make([]string, 0),
		relations:   make([]string, 0),
		shadowUsers: make([]string, 0),
		graphNodes:  make([]string, 0),
		graphEdges:  make([]string, 0),
		errors:      make([]string, 0),
		advisories:  make([]string, 0),
		startTime:   time.Now(),
		statusPhrases: []string{
			"Probing TLS fingerprints...",
			"Analyzing JA3/JA4 signatures...",
			"Traversing DNS record chains...",
			"Harvesting secondary identifiers...",
			"Correlating social graphs...",
			"Scanning for DNS leaks...",
			"Evaluating device entropy...",
			"Executing pivot extraction...",
			"Verifying STIX indicators...",
			"Auditing network telemetry...",
		},
		tabs:      []string{"Overview", "Results"},
		activeTab: 0,
		unread:    make(map[string]bool),
	}
}

func (m Model) Init() tea.Cmd {
	return tea.Batch(m.spinner.Tick, tick())
}

func tick() tea.Cmd {
	return tea.Every(time.Millisecond*500, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}

// syncTabs dynamically builds the available tabs based on data
func (m Model) syncTabs() Model {
	var currentTabName string
	if len(m.tabs) > 0 && m.activeTab < len(m.tabs) {
		currentTabName = m.tabs[m.activeTab]
	}

	nextTabs := []string{"Overview", "Results"}

	if len(m.graphNodes) > 0 || len(m.graphEdges) > 0 {
		nextTabs = append(nextTabs, "Graph")
	}

	if m.fingerbank != nil || len(m.dnsLeaks) > 0 {
		nextTabs = append(nextTabs, "Network")
	}

	if len(m.errors) > 0 || len(m.advisories) > 0 {
		nextTabs = append(nextTabs, "Alerts")
	}

	m.tabs = nextTabs
	m.activeTab = 0 
	for i, t := range m.tabs {
		if t == currentTabName {
			m.activeTab = i
			break
		}
	}
	return m
}

// notifyTab flags a tab as having unseen data
func (m Model) notifyTab(tabName string) Model {
	if len(m.tabs) == 0 || m.tabs[m.activeTab] != tabName {
		m.unread[tabName] = true
	}
	return m
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var (
		cmd  tea.Cmd
		cmds []tea.Cmd
	)

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		// Subtract roughly 12 lines to leave room for the header and footer
		vpHeight := msg.Height - 12
		if vpHeight < 5 {
			vpHeight = 5 // enforce a minimum
		}

		if !m.ready {
			m.viewport = viewport.New(msg.Width, vpHeight)
			m.ready = true
		} else {
			m.viewport.Width = msg.Width
			m.viewport.Height = vpHeight
		}
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "right", "tab":
			if len(m.tabs) > 0 {
				m.activeTab = (m.activeTab + 1) % len(m.tabs)
				m.viewport.GotoTop()
				m.unread[m.tabs[m.activeTab]] = false
			}
		case "left", "shift+tab":
			if len(m.tabs) > 0 {
				m.activeTab = (m.activeTab - 1 + len(m.tabs)) % len(m.tabs)
				m.viewport.GotoTop()
				m.unread[m.tabs[m.activeTab]] = false
			}
		}

	case tickMsg:
		m.phraseIdx = (m.phraseIdx + 1) % len(m.statusPhrases)
		m.liveStatus = m.statusPhrases[m.phraseIdx]
		cmds = append(cmds, tick())
	case spinner.TickMsg:
		m.spinner, cmd = m.spinner.Update(msg)
		cmds = append(cmds, cmd)
	case StatusMsg:
		m.status = string(msg)
	case ProgressMsg:
		m.percent = float64(msg)
		cmds = append(cmds, m.progress.SetPercent(m.percent))
	case progress.FrameMsg:
		newProgressModel, pCmd := m.progress.Update(msg)
		if pm, ok := newProgressModel.(progress.Model); ok {
			m.progress = pm
		}
		cmds = append(cmds, pCmd)

	// Data updates & Notifications
	case ResultItem:
		m.results = append(m.results, msg)
		m = m.notifyTab("Results")
	case TelemetryMsg:
		m.telemetry = string(msg)
	case FingerprintMsg:
		m.fingerprint = string(msg)
	case DeviceTypeMsg:
		m.deviceType = string(msg)
	case RelationMsg:
		m.relations = append(m.relations, string(msg))
	case ShadowUserMsg:
		m.shadowUsers = append(m.shadowUsers, string(msg))
	case HeatmapMsg:
		m.heatmap = string(msg)
	case EmailMsg:
		m.emails = append(m.emails, string(msg))
	case SocialMediaMsg:
		m.socialMedia = append(m.socialMedia, string(msg))
	case GraphMsg:
		m.graphNodes = append(m.graphNodes, msg.Nodes...)
		m.graphEdges = append(m.graphEdges, msg.Edges...)
		m = m.notifyTab("Graph")
	case FingerbankFindingsMsg:
		m.fingerbank = &msg
		m = m.notifyTab("Network")
	case FingerbankStatusMsg:
		m.fbStatus = &msg
	case DNSLeakMsg:
		m.dnsLeaks = msg
		m = m.notifyTab("Network")
	case ErrorMsg:
		m.errors = append(m.errors, string(msg))
		m = m.notifyTab("Alerts")
	case AdvisoryMsg:
		m.advisories = append(m.advisories, string(msg))
		m = m.notifyTab("Alerts")
	}

	if m.ready {
		m.viewport, cmd = m.viewport.Update(msg)
		cmds = append(cmds, cmd)
	}

	m = m.syncTabs()

	return m, tea.Batch(cmds...)
}

func (m Model) View() string {
	if !m.ready {
		return "\n  Initializing TUI...\n"
	}

	// --- 1. HEADER ---
	header := fmt.Sprintf("%s powered by FJ™ Cybertronic Systems\n", styleBlue.Render("OSINT-Nexus"))
	header += styleTitle.Render(fmt.Sprintf("Command Center - Target: %s", m.targetUser)) + "\n\n"

	var renderedTabs []string
	for i, t := range m.tabs {
		if i == m.activeTab {
			renderedTabs = append(renderedTabs, activeTabStyle.Render(t))
		} else if m.unread[t] {
			renderedTabs = append(renderedTabs, unreadTabStyle.Render(fmt.Sprintf("%s •", t)))
		} else {
			renderedTabs = append(renderedTabs, inactiveTabStyle.Render(t))
		}
	}
	header += lipgloss.JoinHorizontal(lipgloss.Top, renderedTabs...) + "\n"

	// --- 2. TAB CONTENT ---
	var tabContent []string

	if len(m.tabs) > 0 {
		switch m.tabs[m.activeTab] {
		case "Overview":
			metrics := []string{
				fmt.Sprintf("Device Type: %s", m.deviceType),
				fmt.Sprintf("Fingerprint: %s", m.fingerprint),
				fmt.Sprintf("Telemetry:   %s", m.telemetry),
				fmt.Sprintf("Heatmap:     %s", m.heatmap),
			}
			if m.fbStatus != nil {
				status := "Disabled"
				if m.fbStatus.Enabled {
					status = fmt.Sprintf("Enabled (Usage: %d)", m.fbStatus.Usage)
				}
				metrics = append(metrics, fmt.Sprintf("Fingerbank:  %s", status))
			}
			tabContent = append(tabContent, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, metrics...)))

			if len(m.relations) > 0 || len(m.shadowUsers) > 0 || len(m.emails) > 0 || len(m.socialMedia) > 0 {
				var infoBody []string
				if len(m.relations) > 0 {
					infoBody = append(infoBody, "Relations:")
					for _, r := range m.relations {
						infoBody = append(infoBody, "  * "+r)
					}
				}
				if len(m.shadowUsers) > 0 {
					infoBody = append(infoBody, "Shadow Users:")
					for _, s := range m.shadowUsers {
						infoBody = append(infoBody, "  * "+s)
					}
				}
				if len(m.emails) > 0 {
					infoBody = append(infoBody, "Emails:")
					for _, e := range m.emails {
						infoBody = append(infoBody, "  * "+e)
					}
				}
				if len(m.socialMedia) > 0 {
					infoBody = append(infoBody, "Social Media:")
					for _, sm := range m.socialMedia {
						infoBody = append(infoBody, "  * "+sm)
					}
				}
				tabContent = append(tabContent, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, infoBody...)))
			}

		case "Results":
			if len(m.results) > 0 {
				var resultsBody []string
				for _, res := range m.results {
					if res.Found {
						resultsBody = append(resultsBody, styleFound.Render(fmt.Sprintf("  ✓ %s", res.Platform)))
					} else if res.Error != "" {
						resultsBody = append(resultsBody, styleUnknown.Render(fmt.Sprintf("  ? %s (Uncertain: %s)", res.Platform, res.Error)))
					} else {
						resultsBody = append(resultsBody, styleMissing.Render(fmt.Sprintf("  ✗ %s (Not Found)", res.Platform)))
					}
				}
				tabContent = append(tabContent, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, resultsBody...)))
			} else {
				tabContent = append(tabContent, "\n  Awaiting scan results...\n")
			}

		case "Graph":
			if len(m.graphNodes) > 0 || len(m.graphEdges) > 0 {
				graphBody := []string{"Relationship Graph:"}
				for _, node := range m.graphNodes {
					graphBody = append(graphBody, styleFound.Render("  • "+node))
				}
				for _, edge := range m.graphEdges {
					graphBody = append(graphBody, styleGray.Render("  → "+edge))
				}
				tabContent = append(tabContent, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, graphBody...)))
			} else {
				tabContent = append(tabContent, "\n  Awaiting graph data...\n")
			}

		case "Network":
			if m.fingerbank != nil {
				fbBody := []string{
					"Fingerbank Findings:",
					fmt.Sprintf("  Device: %s (Score: %d)", m.fingerbank.DeviceName, m.fingerbank.Score),
					fmt.Sprintf("  Vendor: %s", m.fingerbank.Vendor),
					fmt.Sprintf("  Type: %s", m.fingerbank.DeviceType),
					fmt.Sprintf("  OS: %s", m.fingerbank.OperatingSystem),
				}
				if len(m.fingerbank.Vulnerabilities.CveDevices) > 0 || len(m.fingerbank.Vulnerabilities.CveOs) > 0 {
					fbBody = append(fbBody, "  [!] Vulnerabilities Detected")
				}
				tabContent = append(tabContent, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, fbBody...)))
			}
			if len(m.dnsLeaks) > 0 {
				dnsBody := []string{"DNS Leak Results:"}
				for _, res := range m.dnsLeaks {
					if res.Error != "" {
						dnsBody = append(dnsBody, styleUnknown.Render(fmt.Sprintf("  ! %s (Error: %s)", res.URL, res.Error)))
					} else if res.IsLeaking {
						dnsBody = append(dnsBody, styleUnknown.Render(fmt.Sprintf("  ! %s (LEAKING!)", res.URL)))
					} else {
						dnsBody = append(dnsBody, styleFound.Render(fmt.Sprintf("  ✓ %s (Secure)", res.URL)))
					}
				}
				tabContent = append(tabContent, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, dnsBody...)))
			}

		case "Alerts":
			if len(m.advisories) > 0 {
				advStyle := lipgloss.NewStyle().
					Border(lipgloss.RoundedBorder()).
					BorderForeground(colorInfo).
					Foreground(colorInfo).
					Padding(1, 2).
					Margin(1, 0)
				tabContent = append(tabContent, advStyle.Render(lipgloss.JoinVertical(lipgloss.Left, append([]string{"i ADVISORY i"}, m.advisories...)...)))
			}
			if len(m.errors) > 0 {
				errStyle := lipgloss.NewStyle().
					Border(lipgloss.RoundedBorder()).
					BorderForeground(colorUnknown).
					Foreground(colorUnknown).
					Padding(1, 2).
					Margin(1, 0)
				tabContent = append(tabContent, errStyle.Render(lipgloss.JoinVertical(lipgloss.Left, append([]string{"!! SYSTEM ALERTS !!"}, m.errors...)...)))
			}
		}
	}

	m.viewport.SetContent(tabWindowStyle.Render(lipgloss.JoinVertical(lipgloss.Left, tabContent...)))

	// --- 3. FOOTER ---
	elapsed := time.Since(m.startTime)
	var etaStr string
	if m.percent > 0 {
		total := elapsed.Seconds() / m.percent
		remaining := time.Duration(total-elapsed.Seconds()) * time.Second
		etaStr = fmt.Sprintf(" | ETA: %s", remaining.Round(time.Second))
	} else {
		etaStr = " | ETA: Estimating..."
	}

	progressView := lipgloss.JoinHorizontal(lipgloss.Center, m.spinner.View(), " ", m.progress.View(), styleGray.Render(etaStr))
	
	footer := fmt.Sprintf("\n%s\nStatus: %s\n%s\n", progressView, m.status, styleInfo.Render(fmt.Sprintf("Active: %s", m.liveStatus)))
	footer += styleGray.Render("Navigate: ←/→ or Tab/Shift+Tab | Scroll: ↑/↓ | Quit: q")

	return fmt.Sprintf("%s\n%s\n%s", header, m.viewport.View(), footer)
}

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
type TelemetryData struct {
	ActiveSockets int
	BytesSent     int64
	BytesReceived int64
	Latency       time.Duration
}

type TelemetryMsg TelemetryData
type FingerprintMsg string
type DeviceTypeMsg string
type RelationMsg string
type ShadowUserMsg string
type HeatmapData []float64
type HeatmapMsg HeatmapData
type ChartData struct {
	Title  string
	Values []float64
}
type ChartMsg ChartData
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
type DorkResult struct {
	Query string
	URL   string
}
type DorkMsg []DorkResult
type TimezoneMsg string
type DeviceFingerprint struct {
	JA3    string
	JA3S   string
	UserAgent string
}
type DeviceFingerprintMsg DeviceFingerprint
type DNSLeakMsg []DNSLeakResult
type DNSLeakResult struct {
	URL       string
	IsLeaking bool
	Error     string
}
type AnomalyAlertMsg struct {
	SessionID string
	Message   string
	Severity  string
}
type StylometryMsg struct {
	Language           string
	AvgSentenceLength  float64
	AvgWordLength      float64
	PunctuationDensity float64
	VocabularyRichness float64
}
type SessionMsg struct {
	SessionID  string
	ProfileID  string
	DeviceType string
	LastSeen   time.Time
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
	telemetry     TelemetryData
	fingerprint   string
	deviceType    string
	emails        []string
	socialMedia   []string
	relations     []string
	shadowUsers   []string
	heatmap       HeatmapData
	charts        []ChartData
	graphNodes    []string
	graphEdges    []string
	fingerbank    *FingerbankFindingsMsg
	fbStatus      *FingerbankStatusMsg
	dorks         []DorkResult
	timezone      string
	deviceFingerprint DeviceFingerprint
	dnsLeaks      []DNSLeakResult
	anomalyAlerts []AnomalyAlertMsg
	stylometry    []StylometryMsg
	sessions      []SessionMsg
	errors        []string
	advisories    []string
	startTime   time.Time
	percent       float64
	liveStatus    string

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
		heatmap:     make(HeatmapData, 0),
		charts:      make([]ChartData, 0),
		graphNodes:  make([]string, 0),
		graphEdges:  make([]string, 0),
		dorks:       make([]DorkResult, 0),
		timezone:    "Unknown",
		deviceFingerprint: DeviceFingerprint{},
		anomalyAlerts: make([]AnomalyAlertMsg, 0),
		stylometry:    make([]StylometryMsg, 0),
		sessions:      make([]SessionMsg, 0),
		errors:        make([]string, 0),
		advisories:  make([]string, 0),
		startTime:   time.Now(),
		tabs:      []string{"Overview", "Results"},
		activeTab: 0,
		unread:    make(map[string]bool),
	}
}

func (m Model) Init() tea.Cmd {
	return tea.Batch(m.spinner.Tick, tick())
}

func tick() tea.Cmd {
	return tea.Every(time.Second*2, func(t time.Time) tea.Msg {
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

	if len(m.heatmap) > 0 || len(m.charts) > 0 || len(m.relations) > 0 {
		nextTabs = append(nextTabs, "Analysis")
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
		// Dynamic responsive scaling
		vpHeight := msg.Height - 12
		if vpHeight < 5 {
			vpHeight = 5
		}

		m.viewport.Width = msg.Width
		m.viewport.Height = vpHeight
		m.ready = true
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
		case "pgup":
			m.viewport.ViewDown()
		case "pgdown":
			m.viewport.ViewUp()
		case "enter":
			// Placeholder for "select/initiate" action
			m.status = fmt.Sprintf("Selected: %s", m.tabs[m.activeTab])
		}

	case tickMsg:
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
		m.telemetry = TelemetryData(msg)
	case FingerprintMsg:
		m.fingerprint = string(msg)
	case DeviceTypeMsg:
		m.deviceType = string(msg)
	case RelationMsg:
		m.relations = append(m.relations, string(msg))
	case ShadowUserMsg:
		m.shadowUsers = append(m.shadowUsers, string(msg))
	case HeatmapMsg:
		m.heatmap = HeatmapData(msg)
	case ChartMsg:
		m.charts = append(m.charts, ChartData(msg))
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
	case DorkMsg:
		m.dorks = append(m.dorks, msg...)
		m = m.notifyTab("Results")
	case TimezoneMsg:
		m.timezone = string(msg)
	case DeviceFingerprintMsg:
		m.deviceFingerprint = DeviceFingerprint(msg)
	case AnomalyAlertMsg:
		m.anomalyAlerts = append(m.anomalyAlerts, msg)
		m = m.notifyTab("Alerts")
	case StylometryMsg:
		m.stylometry = append(m.stylometry, msg)
		m = m.notifyTab("Analysis")
	case SessionMsg:
		found := false
		for i, s := range m.sessions {
			if s.SessionID == msg.SessionID {
				m.sessions[i] = msg
				found = true
				break
			}
		}
		if !found {
			m.sessions = append(m.sessions, msg)
		}
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

	// --- 0. BRANDING ---
	brandingBox := styleBrand.Render("Powered by FJ™ Cybertronic Systems")

	// --- 1. HEADER ---
	header := brandingBox + "\n" + fmt.Sprintf("%s\n", styleBlue.Render("OSINT-Nexus"))
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
	vr := ViewRendering{m: &m}
	var tabContent []string

	if len(m.tabs) > 0 {
		switch m.tabs[m.activeTab] {
		case "Overview":
			tabContent = vr.Overview()
		case "Results":
			tabContent = vr.Results()
		case "Graph":
			tabContent = vr.Graph()
		case "Analysis":
			tabContent = vr.Analysis()
		case "Network":
			tabContent = vr.Network()
		case "Alerts":
			tabContent = vr.Alerts()
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
	footer += styleGray.Render("Navigate: ←/→ | Scroll: ↑/↓/PgUp/PgDown | Select: Enter | Quit: q")

	return fmt.Sprintf("%s\n%s\n%s", header, m.viewport.View(), footer)
}

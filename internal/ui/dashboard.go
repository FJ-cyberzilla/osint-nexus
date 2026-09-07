package ui

import (
	"fmt"
	"time"

	"github.com/charmbracelet/bubbles/progress"
	"github.com/charmbracelet/bubbles/spinner"
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
	relations     []string
	shadowUsers   []string
	heatmap       string
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
		relations:   make([]string, 0),
		shadowUsers: make([]string, 0),
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

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		if msg.String() == "q" || msg.String() == "ctrl+c" {
			return m, tea.Quit
		}
	case tickMsg:
		m.phraseIdx = (m.phraseIdx + 1) % len(m.statusPhrases)
		m.liveStatus = m.statusPhrases[m.phraseIdx]
		return m, tick()
	case spinner.TickMsg:
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		return m, cmd
	case StatusMsg:
		m.status = string(msg)
		return m, nil
	case ProgressMsg:
		m.percent = float64(msg)
		m.progress.SetPercent(m.percent)
		return m, nil
	case ResultItem:
		m.results = append(m.results, msg)
		return m, nil
	case TelemetryMsg:
		m.telemetry = string(msg)
		return m, nil
	case FingerprintMsg:
		m.fingerprint = string(msg)
		return m, nil
	case DeviceTypeMsg:
		m.deviceType = string(msg)
		return m, nil
	case RelationMsg:
		m.relations = append(m.relations, string(msg))
		return m, nil
	case ShadowUserMsg:
		m.shadowUsers = append(m.shadowUsers, string(msg))
		return m, nil
	case HeatmapMsg:
		m.heatmap = string(msg)
		return m, nil
	case FingerbankFindingsMsg:
		m.fingerbank = &msg
		return m, nil
	case FingerbankStatusMsg:
		m.fbStatus = &msg
		return m, nil
	case DNSLeakMsg:
		m.dnsLeaks = msg
		return m, nil
	case ErrorMsg:
		m.errors = append(m.errors, string(msg))
		return m, nil
	case AdvisoryMsg:
		m.advisories = append(m.advisories, string(msg))
		return m, nil
	}
	return m, nil
}

func (m Model) View() string {
	var body []string

	// Header Panel
	header := fmt.Sprintf("%s powered by FJ™ Cybertronic Systems", styleBlue.Render("OSINT-Nexus"))
	body = append(body, styleBrand.Render(header))
	
	body = append(body, styleTitle.Render(fmt.Sprintf("Command Center - Target: %s", m.targetUser)))
	
	// Metrics Panel
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
	body = append(body, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, metrics...)))
	
	// Spinner + Progress
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
	body = append(body, progressView)
	body = append(body, fmt.Sprintf("Status: %s", m.status))
	body = append(body, styleInfo.Render(fmt.Sprintf("Active: %s", m.liveStatus)))

	// Relations & Shadows Panel
	if len(m.relations) > 0 || len(m.shadowUsers) > 0 {
		var infoBody []string
		if len(m.relations) > 0 {
			infoBody = append(infoBody, "Relations:")
			for _, r := range m.relations { infoBody = append(infoBody, "  * " + r) }
		}
		if len(m.shadowUsers) > 0 {
			infoBody = append(infoBody, "Shadow Users:")
			for _, s := range m.shadowUsers { infoBody = append(infoBody, "  * " + s) }
		}
		body = append(body, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, infoBody...)))
	}

	// Fingerbank Findings Panel
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
		body = append(body, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, fbBody...)))
	}

	// DNS Leak Results
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
		body = append(body, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, dnsBody...)))
	}

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
		body = append(body, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, resultsBody...)))
	}
	
	// Advisory Panel (Conditional)
	if len(m.advisories) > 0 {
		advStyle := lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorInfo).
			Foreground(colorInfo).
			Padding(1, 2).
			Margin(1, 0)
			
		body = append(body, advStyle.Render(lipgloss.JoinVertical(lipgloss.Left, append([]string{"i ADVISORY i"}, m.advisories...)...)))
	}

	// Error Panel (Conditional)
	if len(m.errors) > 0 {
		errStyle := lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorUnknown).
			Foreground(colorUnknown).
			Padding(1, 2).
			Margin(1, 0)
			
		body = append(body, errStyle.Render(lipgloss.JoinVertical(lipgloss.Left, append([]string{"!! SYSTEM ALERTS !!"}, m.errors...)...)))
	}

	// Help line
	body = append(body, styleGray.Render("\nPress 'q' or 'ctrl+c' to cancel and quit"))

	return lipgloss.JoinVertical(lipgloss.Left, body...) + "\n"
}

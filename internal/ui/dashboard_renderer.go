package ui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
)

// ViewRendering encapsulates tab-specific rendering logic.
type ViewRendering struct {
	m *Model
}

func (vr *ViewRendering) Overview() []string {
	metrics := []string{
		fmt.Sprintf("Device Type: %s", vr.m.deviceType),
		fmt.Sprintf("Timezone:    %s", vr.m.timezone),
		fmt.Sprintf("Fingerprint: JA3:%s | JA3S:%s", vr.m.deviceFingerprint.JA3, vr.m.deviceFingerprint.JA3S),
		fmt.Sprintf("User Agent:  %s", vr.m.deviceFingerprint.UserAgent),
		fmt.Sprintf("Telemetry:   [Sockets: %d | Sent: %d B | Rcvd: %d B | Lat: %v]",
			vr.m.telemetry.ActiveSockets, vr.m.telemetry.BytesSent, vr.m.telemetry.BytesReceived, vr.m.telemetry.Latency),
	}
	if vr.m.fbStatus != nil {
		status := "Disabled"
		if vr.m.fbStatus.Enabled {
			status = fmt.Sprintf("Enabled (Usage: %d)", vr.m.fbStatus.Usage)
		}
		metrics = append(metrics, fmt.Sprintf("Fingerbank:  %s", status))
	}
	content := []string{styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, metrics...))}

	if len(vr.m.relations) > 0 || len(vr.m.shadowUsers) > 0 || len(vr.m.emails) > 0 || len(vr.m.socialMedia) > 0 || len(vr.m.dorks) > 0 {
		var infoBody []string
		if len(vr.m.relations) > 0 {
			infoBody = append(infoBody, "Relations:")
			for _, r := range vr.m.relations {
				infoBody = append(infoBody, "  * "+r)
			}
		}
		if len(vr.m.emails) > 0 {
			infoBody = append(infoBody, "Emails:")
			for _, e := range vr.m.emails {
				infoBody = append(infoBody, "  * "+e)
			}
		}
		if len(vr.m.socialMedia) > 0 {
			infoBody = append(infoBody, "Social Media:")
			for _, sm := range vr.m.socialMedia {
				infoBody = append(infoBody, "  * "+sm)
			}
		}
		if len(vr.m.dorks) > 0 {
			infoBody = append(infoBody, "Dork Results:")
			for _, d := range vr.m.dorks {
				infoBody = append(infoBody, fmt.Sprintf("  * Query: %s -> %s", d.Query, d.URL))
			}
		}
		if len(vr.m.shadowUsers) > 0 {
			infoBody = append(infoBody, styleUnknown.Render("Shadow Users:"))
			for _, s := range vr.m.shadowUsers {
				infoBody = append(infoBody, styleUnknown.Render("  * "+s))
			}
		}
		content = append(content, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, infoBody...)))
	}
	return content
}

func (vr *ViewRendering) Results() []string {
	if len(vr.m.results) > 0 {
		var resultsBody []string
		for _, res := range vr.m.results {
			if res.Found {
				resultsBody = append(resultsBody, styleFound.Render(fmt.Sprintf("  ✓ %s", res.Platform)))
			} else if res.Error != "" {
				resultsBody = append(resultsBody, styleUnknown.Render(fmt.Sprintf("  ? %s (Uncertain: %s)", res.Platform, res.Error)))
			} else {
				resultsBody = append(resultsBody, styleMissing.Render(fmt.Sprintf("  ✗ %s (Not Found)", res.Platform)))
			}
		}
		return []string{styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, resultsBody...))}
	}
	return []string{"\n  Awaiting scan results...\n"}
}

func (vr *ViewRendering) Graph() []string {
	if len(vr.m.graphNodes) > 0 || len(vr.m.graphEdges) > 0 {
		graphBody := []string{"Relationship Graph:"}
		for _, node := range vr.m.graphNodes {
			graphBody = append(graphBody, styleFound.Render("  • "+node))
		}
		for _, edge := range vr.m.graphEdges {
			graphBody = append(graphBody, styleGray.Render("  → "+edge))
		}
		return []string{styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, graphBody...))}
	}
	return []string{"\n  Awaiting graph data...\n"}
}

func (vr *ViewRendering) Analysis() []string {
	var analysisBody []string
	if len(vr.m.relations) > 0 {
		analysisBody = append(analysisBody, "Relations:")
		for _, r := range vr.m.relations {
			analysisBody = append(analysisBody, "  * "+r)
		}
	}
	if len(vr.m.heatmap) > 0 {
		analysisBody = append(analysisBody, "\nHeatmap Intensity:")
		hMap := ""
		for _, v := range vr.m.heatmap {
			if v > 0.8 {
				hMap += "█"
			} else if v > 0.5 {
				hMap += "▓"
			} else {
				hMap += "░"
			}
		}
		analysisBody = append(analysisBody, styleUnknown.Render(hMap))
	}
	for _, c := range vr.m.charts {
		analysisBody = append(analysisBody, fmt.Sprintf("\n%s:", c.Title))
		cBar := ""
		for _, v := range c.Values {
			cBar += fmt.Sprintf("%.1f|", v)
		}
		analysisBody = append(analysisBody, styleBlue.Render(cBar))
	}
	return []string{styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, analysisBody...))}
}

func (vr *ViewRendering) Network() []string {
	var networkBody []string
	if vr.m.fingerbank != nil {
		fbBody := []string{
			"Fingerbank Findings:",
			fmt.Sprintf("  Device: %s (Score: %d)", vr.m.fingerbank.DeviceName, vr.m.fingerbank.Score),
			fmt.Sprintf("  Vendor: %s", vr.m.fingerbank.Vendor),
			fmt.Sprintf("  Type: %s", vr.m.fingerbank.DeviceType),
			fmt.Sprintf("  OS: %s", vr.m.fingerbank.OperatingSystem),
		}
		if len(vr.m.fingerbank.Vulnerabilities.CveDevices) > 0 || len(vr.m.fingerbank.Vulnerabilities.CveOs) > 0 {
			fbBody = append(fbBody, "  [!] Vulnerabilities Detected")
		}
		networkBody = append(networkBody, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, fbBody...)))
	}
	if len(vr.m.dnsLeaks) > 0 {
		dnsBody := []string{"DNS Leak Results:"}
		for _, res := range vr.m.dnsLeaks {
			if res.Error != "" {
				dnsBody = append(dnsBody, styleUnknown.Render(fmt.Sprintf("  ! %s (Error: %s)", res.URL, res.Error)))
			} else if res.IsLeaking {
				dnsBody = append(dnsBody, styleUnknown.Render(fmt.Sprintf("  ! %s (LEAKING!)", res.URL)))
			} else {
				dnsBody = append(dnsBody, styleFound.Render(fmt.Sprintf("  ✓ %s (Secure)", res.URL)))
			}
		}
		networkBody = append(networkBody, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, dnsBody...)))
	}
	return networkBody
}

func (vr *ViewRendering) Alerts() []string {
	var alertBody []string
	if len(vr.m.advisories) > 0 {
		advStyle := lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorInfo).
			Foreground(colorInfo).
			Padding(1, 2).
			Margin(1, 0)
		alertBody = append(alertBody, advStyle.Render(lipgloss.JoinVertical(lipgloss.Left, append([]string{"i ADVISORY i"}, vr.m.advisories...)...)))
	}
	if len(vr.m.errors) > 0 {
		errStyle := lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorUnknown).
			Foreground(colorUnknown).
			Padding(1, 2).
			Margin(1, 0)
		alertBody = append(alertBody, errStyle.Render(lipgloss.JoinVertical(lipgloss.Left, append([]string{"!! SYSTEM ALERTS !!"}, vr.m.errors...)...)))
	}
	return alertBody
}

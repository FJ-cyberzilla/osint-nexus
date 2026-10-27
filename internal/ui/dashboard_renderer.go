package ui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
)

// ViewRendering encapsulates tab-specific rendering logic using modular panels and system status components.
type ViewRendering struct {
	m *Model
}

func (vr *ViewRendering) Overview() []string {
	var content []string

	// 1. Omni-Masquerade Central Nerve Status Panel
	content = append(content, RenderOmniMasqueradePanel(vr.m))

	// 2. App Status & Engine Indicators (Local System & Runtime)
	content = append(content, RenderSysStatus(vr.m)...)

	// 3. Target Username Footprint & Fingerprint Relation Map
	content = append(content, RenderFootprintFingerprintRelationMap(vr.m))

	// 4. Unified System Telemetry, Errors, Issues & Fallback States
	content = append(content, RenderUnifiedErrorsAndAdvisories(vr.m))

	// 5. Final Findings Summary (if operation finished) or Target Intelligence
	if vr.m.percent >= 1.0 || vr.m.status == "Scan completed." || vr.m.status == "Operation finished. Reconnaissance completed successfully." {
		content = append(content, RenderFinalFindingsPanel(vr.m))
	} else {
		if len(vr.m.relations) > 0 || len(vr.m.shadowUsers) > 0 || len(vr.m.emails) > 0 || len(vr.m.socialMedia) > 0 || len(vr.m.dorks) > 0 {
			var infoBody []string
			if len(vr.m.emails) > 0 {
				infoBody = append(infoBody, "Emails Discovered:")
				for _, e := range vr.m.emails {
					infoBody = append(infoBody, "  * "+e)
				}
			}
			if len(vr.m.socialMedia) > 0 {
				infoBody = append(infoBody, "Social Media Links:")
				for _, sm := range vr.m.socialMedia {
					infoBody = append(infoBody, "  * "+sm)
				}
			}
			if len(vr.m.dorks) > 0 {
				infoBody = append(infoBody, "Dork Intelligence:")
				for _, d := range vr.m.dorks {
					infoBody = append(infoBody, fmt.Sprintf("  * Query: %s -> %s", d.Query, d.URL))
				}
			}
			content = append(content, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, infoBody...)))
		} else {
			content = append(content, styleBox.Render(fmt.Sprintf("Target Intelligence & Reconnaissance:\n  Executing probes for target '%s'...", vr.m.targetUser)))
		}
	}

	return content
}

func (vr *ViewRendering) Results() []string {
	var content []string

	if vr.m.percent >= 1.0 || vr.m.status == "Scan completed." || vr.m.status == "Operation finished. Reconnaissance completed successfully." {
		content = append(content, RenderFinalFindingsPanel(vr.m))
	}

	if len(vr.m.results) > 0 {
		var resultsBody []string
		resultsBody = append(resultsBody, fmt.Sprintf("Platform Probes & Results (Target: %s):", vr.m.targetUser))
		for _, res := range vr.m.results {
			if res.Found {
				resultsBody = append(resultsBody, styleFound.Render(fmt.Sprintf("  ✓ %s: Found (Account Active)", res.Platform)))
			} else if res.Error != "" {
				resultsBody = append(resultsBody, styleUnknown.Render(fmt.Sprintf("  ? %s: Error (%s)", res.Platform, res.Error)))
			} else {
				resultsBody = append(resultsBody, styleMissing.Render(fmt.Sprintf("  ✗ %s: Not Found (404 / Inactive)", res.Platform)))
			}
		}
		content = append(content, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, resultsBody...)))
	}

	if len(vr.m.dorks) > 0 {
		content = append(content, RenderDorkPanel(vr.m))
	}

	if len(content) == 0 {
		return []string{styleBox.Render(fmt.Sprintf("Scan Results Panel (Target: %s):\n  Scanning platforms... (Progress: %.0f%%)", vr.m.targetUser, vr.m.percent*100))}
	}
	return content
}

func (vr *ViewRendering) Graph() []string {
	if len(vr.m.graphNodes) > 0 || len(vr.m.graphEdges) > 0 {
		graphBody := []string{"Relationship Graph & Intelligence Map:"}
		for _, node := range vr.m.graphNodes {
			graphBody = append(graphBody, styleFound.Render("  • "+node))
		}
		for _, edge := range vr.m.graphEdges {
			graphBody = append(graphBody, styleGray.Render("  → "+edge))
		}
		return []string{styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, graphBody...))}
	}
	if vr.m.percent >= 1.0 || vr.m.status == "Scan completed." {
		return []string{styleBox.Render(fmt.Sprintf("Relationship Graph Panel:\n  No relationship graph nodes or edges generated for target '%s'.", vr.m.targetUser))}
	}
	return []string{styleBox.Render(fmt.Sprintf("Relationship Graph Panel:\n  Awaiting graph data for target '%s'...", vr.m.targetUser))}
}

func (vr *ViewRendering) Analysis() []string {
	var analysisBody []string
	analysisBody = append(analysisBody, "Analysis & Pivoting Panel:")
	if len(vr.m.relations) > 0 {
		analysisBody = append(analysisBody, "Relations:")
		for _, r := range vr.m.relations {
			analysisBody = append(analysisBody, "  * "+r)
		}
	}
	if len(vr.m.stylometry) > 0 {
		analysisBody = append(analysisBody, "\nStylometric Analysis:")
		for _, s := range vr.m.stylometry {
			analysisBody = append(analysisBody, fmt.Sprintf("  [%s] AvgWordLen: %.1f | PunctDensity: %.2f | Richness: %.2f",
				s.Language, s.AvgWordLength, s.PunctuationDensity, s.VocabularyRichness))
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
	if len(vr.m.relations) == 0 && len(vr.m.stylometry) == 0 && len(vr.m.heatmap) == 0 && len(vr.m.charts) == 0 {
		if vr.m.percent >= 1.0 || vr.m.status == "Scan completed." {
			analysisBody = append(analysisBody, fmt.Sprintf("  No analysis metrics, heatmap, charts, or relations generated for target '%s'.", vr.m.targetUser))
		} else {
			analysisBody = append(analysisBody, fmt.Sprintf("  Awaiting analysis data for target '%s'...", vr.m.targetUser))
		}
	}
	return []string{styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, analysisBody...))}
}

func (vr *ViewRendering) Network() []string {
	var networkBody []string
	networkBody = append(networkBody, "Network & Fingerbank Panel:")
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
	if vr.m.fingerbank == nil && len(vr.m.dnsLeaks) == 0 {
		if vr.m.percent >= 1.0 || vr.m.status == "Scan completed." {
			networkBody = append(networkBody, fmt.Sprintf("  No Fingerbank hardware findings or DNS leaks recorded for target '%s'.", vr.m.targetUser))
		} else {
			networkBody = append(networkBody, fmt.Sprintf("  Awaiting network probes for target '%s'...", vr.m.targetUser))
		}
	}
	return []string{styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, networkBody...))}
}

func (vr *ViewRendering) Alerts() []string {
	var alertBody []string
	alertBody = append(alertBody, "Security Alerts & System Messages Panel:")
	if len(vr.m.anomalyAlerts) > 0 {
		var anomalyBody []string
		anomalyBody = append(anomalyBody, "Anomaly Detection Alerts:")
		for _, a := range vr.m.anomalyAlerts {
			severityStyle := styleInfo
			if a.Severity == "WARNING" {
				severityStyle = styleUnknown
			} else if a.Severity == "CRITICAL" {
				severityStyle = styleUnknown.Bold(true)
			}
			anomalyBody = append(anomalyBody, severityStyle.Render(fmt.Sprintf("  [%s] %s: %s", a.Severity, a.SessionID[:8], a.Message)))
		}
		alertBody = append(alertBody, styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, anomalyBody...)))
	}
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
	if len(vr.m.anomalyAlerts) == 0 && len(vr.m.advisories) == 0 && len(vr.m.errors) == 0 {
		if vr.m.percent >= 1.0 || vr.m.status == "Scan completed." {
			alertBody = append(alertBody, styleBox.Render(fmt.Sprintf("  No security anomalies, advisories, or system errors recorded for target '%s'.", vr.m.targetUser)))
		} else {
			alertBody = append(alertBody, styleBox.Render(fmt.Sprintf("  Monitoring alerts and telemetry for target '%s'...", vr.m.targetUser)))
		}
	}
	return alertBody
}

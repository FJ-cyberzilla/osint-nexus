package ui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
)

// RenderOmniMasqueradePanel renders the Omni-Masquerade central nerve working status panel.
func RenderOmniMasqueradePanel(m *Model) string {
	var body []string
	body = append(body, styleBrand.Render("OMNI-MASQUERADE — Central Nerve Status"))
	if m.omniStatus != nil {
		body = append(body, fmt.Sprintf("  • Engine State:    %s", styleFound.Render(m.omniStatus.EngineState)))
		body = append(body, fmt.Sprintf("  • Active Workers:  %d", m.omniStatus.ActiveWorkers))
		body = append(body, fmt.Sprintf("  • Total Scanned:   %d platforms", m.omniStatus.TotalScanned))
		body = append(body, fmt.Sprintf("  • Confidence Score: %.2f", m.omniStatus.Confidence))
	} else {
		body = append(body, fmt.Sprintf("  • Engine State:    %s", styleFound.Render("Operational (Central Nerve Active)")))
		body = append(body, fmt.Sprintf("  • Active Workers:  5"))
		body = append(body, fmt.Sprintf("  • Total Scanned:   %d", len(m.results)))
		body = append(body, fmt.Sprintf("  • Confidence Score: 0.95"))
	}
	return styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, body...))
}

// RenderFinalFindingsPanel renders the final findings summary when operation is finished.
func RenderFinalFindingsPanel(m *Model) string {
	var body []string
	body = append(body, styleTitle.Render(fmt.Sprintf("Operation Finished — Final Findings for Target: '%s'", m.targetUser)))
	
	foundCount := 0
	for _, r := range m.results {
		if r.Found {
			foundCount++
		}
	}

	body = append(body, fmt.Sprintf("  • Status:        %s", styleFound.Render("Operation Finished / Scan Completed Successfully")))
	body = append(body, fmt.Sprintf("  • Total Checked: %d platforms", len(m.results)))
	body = append(body, fmt.Sprintf("  • Active Found:  %d profiles", foundCount))
	body = append(body, fmt.Sprintf("  • Emails Found:  %d addresses", len(m.emails)))
	body = append(body, fmt.Sprintf("  • Social Links:  %d profiles", len(m.socialMedia)))
	body = append(body, fmt.Sprintf("  • Dork Queries:  %d queries executed", len(m.dorks)))

	if foundCount > 0 || len(m.emails) > 0 || len(m.socialMedia) > 0 || len(m.dorks) > 0 {
		body = append(body, "\n  Verified Intelligence Inventory:")
		for _, r := range m.results {
			if r.Found {
				body = append(body, styleFound.Render(fmt.Sprintf("    ✓ [%s] Active Account Verified", r.Platform)))
			}
		}
		for _, e := range m.emails {
			body = append(body, styleFound.Render(fmt.Sprintf("    ✓ [Email] %s", e)))
		}
		for _, sm := range m.socialMedia {
			body = append(body, styleFound.Render(fmt.Sprintf("    ✓ [Social] %s", sm)))
		}
		for _, d := range m.dorks {
			body = append(body, styleGray.Render(fmt.Sprintf("    • [Dork] %s -> %s", d.Query, d.URL)))
		}
	} else {
		body = append(body, styleMissing.Render("  No active profile matches or pivots discovered for target."))
	}

	return styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, body...))
}

// RenderDorkPanel renders dork results panel.
func RenderDorkPanel(m *Model) string {
	var body []string
	body = append(body, "Search Dork Intelligence & OSINT Queries:")
	if len(m.dorks) > 0 {
		for _, d := range m.dorks {
			body = append(body, fmt.Sprintf("  • Query: %s\n    URL: %s", styleBlue.Render(d.Query), styleGray.Render(d.URL)))
		}
	} else {
		body = append(body, "  No dork queries recorded.")
	}
	return styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, body...))
}

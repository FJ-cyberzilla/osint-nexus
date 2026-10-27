package ui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
)

// RenderSysStatus renders application status, local system indicators, and engine telemetry.
func RenderSysStatus(m *Model) []string {
	var body []string
	body = append(body, "App Status & Engine Indicators (Local System & Runtime):")
	body = append(body, fmt.Sprintf("  • App State:      %s", "Operational / Command Center Active"))
	body = append(body, fmt.Sprintf("  • Local Device:   %s", m.deviceType))
	body = append(body, fmt.Sprintf("  • Timezone:       %s", m.timezone))
	body = append(body, fmt.Sprintf("  • TLS Fingerprint: JA3:%s | JA3S:%s", m.deviceFingerprint.JA3, m.deviceFingerprint.JA3S))
	body = append(body, fmt.Sprintf("  • Network Sockets: [Active: %d | Sent: %d B | Rcvd: %d B | Lat: %v]",
		m.telemetry.ActiveSockets, m.telemetry.BytesSent, m.telemetry.BytesReceived, m.telemetry.Latency))

	if m.fbStatus != nil {
		status := "Disabled"
		if m.fbStatus.Enabled {
			status = fmt.Sprintf("Enabled (Usage: %d)", m.fbStatus.Usage)
		}
		body = append(body, fmt.Sprintf("  • Fingerbank:     %s", status))
	}

	if len(m.sessions) > 0 {
		body = append(body, fmt.Sprintf("  • Active Sessions: %d", len(m.sessions)))
	}

	return []string{styleBox.Render(lipgloss.JoinVertical(lipgloss.Left, body...))}
}

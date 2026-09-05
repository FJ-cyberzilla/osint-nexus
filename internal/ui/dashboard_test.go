package ui

import (
	"strings"
	"testing"
)

func TestNewModel(t *testing.T) {
	m := NewModel()
	if m.status != "Starting OSINT-Nexus..." {
		t.Errorf("Expected initial status, got %s", m.status)
	}
}

func TestModel_View(t *testing.T) {
	m := NewModel()
	view := m.View()

	if !strings.Contains(view, "OSINT-Nexus") || !strings.Contains(view, "Command Center") {
		t.Errorf("View does not contain branding or title")
	}
}

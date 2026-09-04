package exporter

import (
	"testing"

	"github.com/osint-nexus/internal/types"
)

func TestExportIdentityProfile(t *testing.T) {
	exporter := NewSTIXExporter()
	profile := &types.IdentityProfile{
		Username: "testuser",
	}

	bundle, err := exporter.ExportIdentityProfile(profile)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if len(bundle.Objects) != 1 {
		t.Fatalf("Expected 1 object, got %d", len(bundle.Objects))
	}

	identity, ok := bundle.Objects[0].(STIXIdentity)
	if !ok {
		t.Fatal("Expected STIXIdentity object")
	}

	if identity.Name != "testuser" {
		t.Errorf("Expected name 'testuser', got '%s'", identity.Name)
	}
}

func TestExportIOC(t *testing.T) {
	exporter := NewSTIXExporter()
	ioc := &types.ExtractedIOC{
		Type:  types.IOCTypeIPv4,
		Value: "1.2.3.4",
	}

	bundle, err := exporter.ExportIOC(ioc)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if len(bundle.Objects) != 1 {
		t.Fatalf("Expected 1 object, got %d", len(bundle.Objects))
	}

	indicator, ok := bundle.Objects[0].(STIXIndicator)
	if !ok {
		t.Fatal("Expected STIXIndicator object")
	}

	if indicator.Name != "ipv4" {
		t.Errorf("Expected name 'ipv4', got '%s'", indicator.Name)
	}
	expectedPattern := "[ipv4:value = '1.2.3.4']"
	if indicator.Pattern != expectedPattern {
		t.Errorf("Expected pattern '%s', got '%s'", expectedPattern, indicator.Pattern)
	}
}

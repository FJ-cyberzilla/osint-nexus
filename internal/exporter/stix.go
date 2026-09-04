package exporter

import (
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/osint-nexus/internal/types"
)

// STIXIdentity represents a STIX 2.1 Identity object.
type STIXIdentity struct {
	Type          string `json:"type"`
	ID            string `json:"id"`
	Created       string `json:"created"`
	Name          string `json:"name"`
	Description   string `json:"description,omitempty"`
	IdentityClass string `json:"identity_class"`
}

// STIXIndicator represents a STIX 2.1 Indicator object.
type STIXIndicator struct {
	Type        string `json:"type"`
	ID          string `json:"id"`
	Created     string `json:"created"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
	PatternType string `json:"pattern_type"`
	Pattern     string `json:"pattern"`
}

// STIXBundle represents a STIX 2.1 Bundle.
type STIXBundle struct {
	Type    string `json:"type"`
	ID      string `json:"id"`
	Objects []any  `json:"objects"`
}

// STIXExporter handles export of scan data to STIX 2.1 format.
type STIXExporter struct{}

// NewSTIXExporter initializes a new STIXExporter.
func NewSTIXExporter() *STIXExporter {
	return &STIXExporter{}
}

// ExportIdentityProfile converts an IdentityProfile into a STIXBundle.
func (e *STIXExporter) ExportIdentityProfile(profile *types.IdentityProfile) (*STIXBundle, error) {
	identity := STIXIdentity{
		Type:          "identity",
		ID:            fmt.Sprintf("identity--%s", uuid.New().String()),
		Created:       time.Now().UTC().Format(time.RFC3339),
		Name:          profile.Username,
		IdentityClass: "individual",
	}

	bundle := &STIXBundle{
		Type:    "bundle",
		ID:      fmt.Sprintf("bundle--%s", uuid.New().String()),
		Objects: []any{identity},
	}

	return bundle, nil
}

// ExportIOC converts an ExtractedIOC into a STIXBundle.
func (e *STIXExporter) ExportIOC(ioc *types.ExtractedIOC) (*STIXBundle, error) {
	indicator := STIXIndicator{
		Type:        "indicator",
		ID:          fmt.Sprintf("indicator--%s", uuid.New().String()),
		Created:     time.Now().UTC().Format(time.RFC3339),
		Name:        string(ioc.Type),
		PatternType: "stix",
		Pattern:     fmt.Sprintf("[%s:value = '%s']", ioc.Type, ioc.Value),
	}

	bundle := &STIXBundle{
		Type:    "bundle",
		ID:      fmt.Sprintf("bundle--%s", uuid.New().String()),
		Objects: []any{indicator},
	}

	return bundle, nil
}

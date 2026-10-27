package exporter

import (
	"fmt"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/google/uuid"
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

// STIXRelationship represents a STIX 2.1 Relationship object linking source and target.
type STIXRelationship struct {
	Type           string `json:"type"`
	ID             string `json:"id"`
	Created        string `json:"created"`
	RelationshipRef string `json:"relationship_type"`
	SourceRef      string `json:"source_ref"`
	TargetRef      string `json:"target_ref"`
}

// STIXCampaign represents a STIX 2.1 Campaign object.
type STIXCampaign struct {
	Type        string `json:"type"`
	ID          string `json:"id"`
	Created     string `json:"created"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
}

// STIXBundle represents a STIX 2.1 Bundle.
type STIXBundle struct {
	Type          string             `json:"type"`
	ID            string             `json:"id"`
	Identities    []STIXIdentity     `json:"identities,omitempty"`
	Indicators    []STIXIndicator    `json:"indicators,omitempty"`
	Relationships []STIXRelationship `json:"relationships,omitempty"`
	Campaigns     []STIXCampaign     `json:"campaigns,omitempty"`
}

// STIXExporter handles export of scan data to STIX 2.1 format.
type STIXExporter struct{}

// NewSTIXExporter initializes a new STIXExporter.
func NewSTIXExporter() *STIXExporter {
	return &STIXExporter{}
}

// ExportIdentityProfile converts an IdentityProfile into a STIXBundle.
func (e *STIXExporter) ExportIdentityProfile(profile *types.IdentityProfile) (*STIXBundle, error) {
	identityID := fmt.Sprintf("identity--%s", uuid.New().String())
	identity := STIXIdentity{
		Type:          "identity",
		ID:            identityID,
		Created:       time.Now().UTC().Format(time.RFC3339),
		Name:          profile.Username,
		IdentityClass: "individual",
	}

	bundle := &STIXBundle{
		Type:       "bundle",
		ID:         fmt.Sprintf("bundle--%s", uuid.New().String()),
		Identities: []STIXIdentity{identity},
	}

	return bundle, nil
}

// ExportIOC converts an ExtractedIOC into a STIXBundle.
func (e *STIXExporter) ExportIOC(ioc *types.ExtractedIOC) (*STIXBundle, error) {
	indicatorID := fmt.Sprintf("indicator--%s", uuid.New().String())
	indicator := STIXIndicator{
		Type:        "indicator",
		ID:          indicatorID,
		Created:     time.Now().UTC().Format(time.RFC3339),
		Name:        string(ioc.Type),
		PatternType: "stix",
		Pattern:     fmt.Sprintf("[%s:value = '%s']", ioc.Type, ioc.Value),
	}

	bundle := &STIXBundle{
		Type:       "bundle",
		ID:         fmt.Sprintf("bundle--%s", uuid.New().String()),
		Indicators: []STIXIndicator{indicator},
	}

	return bundle, nil
}

// ExportRelationship links two STIX objects with a relationship type.
func (e *STIXExporter) ExportRelationship(sourceRef, targetRef, relType string) (*STIXBundle, error) {
	relID := fmt.Sprintf("relationship--%s", uuid.New().String())
	rel := STIXRelationship{
		Type:            "relationship",
		ID:              relID,
		Created:         time.Now().UTC().Format(time.RFC3339),
		RelationshipRef: relType,
		SourceRef:       sourceRef,
		TargetRef:       targetRef,
	}

	bundle := &STIXBundle{
		Type:          "bundle",
		ID:            fmt.Sprintf("bundle--%s", uuid.New().String()),
		Relationships: []STIXRelationship{rel},
	}

	return bundle, nil
}

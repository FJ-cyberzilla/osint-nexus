package types

// FingerprintPayload defines the contract for fingerprint data payloads.
type FingerprintPayload interface {
	PayloadType() string
}

// FingerprintData represents structured fingerprint information.
type FingerprintData struct {
	Type    string             `json:"type" yaml:"type"`
	Payload FingerprintPayload `json:"payload" yaml:"payload"`
}

// FingerprintResult holds the outcome of a specific fingerprinting strategy.
type FingerprintResult struct {
	Name       string          `json:"name" yaml:"name"`
	Data       FingerprintData `json:"data" yaml:"data"`
	Confidence float64         `json:"confidence" yaml:"confidence"`
}

// GraphNode represents an entity in the relationship graph.
type GraphNode struct {
	ID       string `json:"id" yaml:"id"`
	Username string `json:"username" yaml:"username"`
	Platform string `json:"platform" yaml:"platform"`
}

// GraphEdge represents a relationship between two nodes.
type GraphEdge struct {
	SourceID string `json:"source_id" yaml:"source_id"`
	TargetID string `json:"target_id" yaml:"target_id"`
	Type     string `json:"type" yaml:"type"` // e.g., "follows", "interacts"
}

package types

// FingerprintPayload defines the contract for fingerprint data payloads.
type FingerprintPayload interface {
	PayloadType() string
}

// FingerprintData represents structured fingerprint information.
type FingerprintData struct {
	Type    string             `json:"type"`
	Payload FingerprintPayload `json:"payload"`
}

// FingerprintResult holds the outcome of a specific fingerprinting strategy.
type FingerprintResult struct {
	Name       string          `json:"name"`
	Data       FingerprintData `json:"data"`
	Confidence float64         `json:"confidence"`
}

// GraphNode represents an entity in the relationship graph.
type GraphNode struct {
	ID       string `json:"id"`
	Username string `json:"username"`
	Platform string `json:"platform"`
}

// GraphEdge represents a relationship between two nodes.
type GraphEdge struct {
	SourceID string `json:"source_id"`
	TargetID string `json:"target_id"`
	Type     string `json:"type"` // e.g., "follows", "interacts"
}

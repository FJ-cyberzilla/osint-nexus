package types

import "time"

type Account struct {
	ID       string  `json:"id"`
	Username *string `json:"username,omitempty"`
	Platform *string `json:"platform,omitempty"`
}

type Node struct {
	ID       string `json:"id"`
	NodeType string `json:"node_type"`
}

type Edge struct {
	Source           string `json:"source"`
	Target           string `json:"target"`
	RelationshipType string `json:"relationship_type"`
}

type RelationshipGraph struct {
	Nodes []Node `json:"nodes"`
	Edges []Edge `json:"edges"`
}

type TimelineEvent struct {
	Timestamp   time.Time `json:"timestamp"`
	Source      string    `json:"source"`
	EventType   string    `json:"event_type"`
	Description string    `json:"description"`
}

type Timeline struct {
	Events []TimelineEvent `json:"events"`
}

type CorrelationDetail struct {
	SourceNodeID string  `json:"source_node_id"`
	TargetNodeID string  `json:"target_node_id"`
	Confidence   float64 `json:"confidence"`
	Methodology  string  `json:"methodology"`
}

type Correlations struct {
	Details []CorrelationDetail `json:"details"`
}

type IdentityProfile struct {
	Username        string             `json:"username"`
	Accounts        []Account          `json:"accounts"`
	Relationships   RelationshipGraph  `json:"relationships"`
	Timeline        *Timeline          `json:"timeline,omitempty"`
	Correlations    *Correlations      `json:"correlations,omitempty"`
	ConfidenceScore float64            `json:"confidence_score"`
}

package types

import (
	"encoding/json"
	"testing"
	"time"
)

func TestIdentityProfile_JSON(t *testing.T) {
	now := time.Now().UTC().Truncate(time.Second)
	
	username := "test_user"
	platform := "github"
	
	profile := IdentityProfile{
		Username: "test_user",
		Accounts: []Account{
			{ID: "1", Username: &username, Platform: &platform},
		},
		Relationships: RelationshipGraph{
			Nodes: []Node{{ID: "1", NodeType: "user"}},
			Edges: []Edge{{Source: "1", Target: "2", RelationshipType: "follows"}},
		},
		Timeline: &Timeline{
			Events: []TimelineEvent{
				{Timestamp: now, Source: "test", EventType: "created", Description: "test description"},
			},
		},
		ConfidenceScore: 0.95,
	}

	data, err := json.Marshal(profile)
	if err != nil {
		t.Fatalf("Failed to marshal IdentityProfile: %v", err)
	}

	var decoded IdentityProfile
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Failed to unmarshal IdentityProfile: %v", err)
	}

	if decoded.Username != profile.Username {
		t.Errorf("Expected username %s, got %s", profile.Username, decoded.Username)
	}
	
	if len(decoded.Accounts) != 1 {
		t.Errorf("Expected 1 account, got %d", len(decoded.Accounts))
	}
	
	if decoded.Timeline == nil || len(decoded.Timeline.Events) != 1 {
		t.Errorf("Timeline marshaling failed")
	}

	if !decoded.Timeline.Events[0].Timestamp.Equal(now) {
		t.Errorf("Timestamp mismatch: expected %v, got %v", now, decoded.Timeline.Events[0].Timestamp)
	}
}

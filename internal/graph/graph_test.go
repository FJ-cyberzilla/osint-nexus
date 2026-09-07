package graph

import (
	"testing"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

func TestGraph_AddNode(t *testing.T) {
	g := NewGraph()
	node := &types.GraphNode{ID: "1", Username: "user1", Platform: "platform1"}

	if err := g.AddNode(node); err != nil {
		t.Fatalf("failed to add node: %v", err)
	}

	if err := g.AddNode(node); err == nil {
		t.Error("expected error when adding duplicate node, got nil")
	}
}

func TestGraph_AddEdge(t *testing.T) {
	g := NewGraph()
	node1 := &types.GraphNode{ID: "1", Username: "user1", Platform: "platform1"}
	node2 := &types.GraphNode{ID: "2", Username: "user2", Platform: "platform2"}

	g.AddNode(node1)
	g.AddNode(node2)

	edge := types.GraphEdge{SourceID: "1", TargetID: "2", Type: "follows"}

	if err := g.AddEdge(edge); err != nil {
		t.Fatalf("failed to add edge: %v", err)
	}

	// Test missing node
	invalidEdge := types.GraphEdge{SourceID: "1", TargetID: "3", Type: "follows"}
	if err := g.AddEdge(invalidEdge); err == nil {
		t.Error("expected error when adding edge with missing node, got nil")
	}
}

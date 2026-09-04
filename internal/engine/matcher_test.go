package engine

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/graph"
	"github.com/osint-nexus/internal/types"
)

func TestMatcher_FindPath(t *testing.T) {
	g := graph.NewGraph()
	g.AddNode(&types.GraphNode{ID: "A"})
	g.AddNode(&types.GraphNode{ID: "B"})
	g.AddNode(&types.GraphNode{ID: "C"})
	g.AddNode(&types.GraphNode{ID: "D"})

	// Setup graph: A -> B -> C, B -> D
	g.AddEdge(types.GraphEdge{SourceID: "A", TargetID: "B"})
	g.AddEdge(types.GraphEdge{SourceID: "B", TargetID: "C"})
	g.AddEdge(types.GraphEdge{SourceID: "B", TargetID: "D"})

	matcher := NewMatcher(g)

	// Test: Path A -> B -> C
	path, err := matcher.FindPath(context.Background(), "A", "C")
	if err != nil {
		t.Fatalf("FindPath failed: %v", err)
	}
	if len(path) != 3 || path[0] != "A" || path[1] != "B" || path[2] != "C" {
		t.Errorf("Expected [A B C], got %v", path)
	}

	// Test: Path A -> B -> D
	path, err = matcher.FindPath(context.Background(), "A", "D")
	if err != nil {
		t.Fatalf("FindPath failed: %v", err)
	}
	if len(path) != 3 || path[0] != "A" || path[1] != "B" || path[2] != "D" {
		t.Errorf("Expected [A B D], got %v", path)
	}

	// Test: No path
	g.AddNode(&types.GraphNode{ID: "E"})
	path, err = matcher.FindPath(context.Background(), "A", "E")
	if err != nil {
		t.Fatalf("FindPath failed: %v", err)
	}
	if path != nil {
		t.Errorf("Expected nil path, got %v", path)
	}
}

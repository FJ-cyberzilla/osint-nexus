package engine

import (
	"context"
	"testing"

	"github.com/FJ-cyberzilla/osint-nexus/internal/graph"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

func TestPivoter_Pivot(t *testing.T) {
	g := graph.NewGraph()
	g.AddNode(&types.GraphNode{ID: "A"})
	g.AddNode(&types.GraphNode{ID: "B"})
	g.AddNode(&types.GraphNode{ID: "C"})

	g.AddEdge(types.GraphEdge{SourceID: "A", TargetID: "B"})
	g.AddEdge(types.GraphEdge{SourceID: "B", TargetID: "C"})

	pivoter := NewPivoter(g)

	// Test: Pivot from A
	related, err := pivoter.Pivot(context.Background(), "A")
	if err != nil {
		t.Fatalf("Pivot failed: %v", err)
	}
	if len(related) != 1 || related[0] != "B" {
		t.Errorf("Expected [B], got %v", related)
	}

	// Test: Pivot from B
	related, err = pivoter.Pivot(context.Background(), "B")
	if err != nil {
		t.Fatalf("Pivot failed: %v", err)
	}
	if len(related) != 2 {
		t.Errorf("Expected 2 related, got %d", len(related))
	}
}

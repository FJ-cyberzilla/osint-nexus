package engine

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/graph"
	"github.com/osint-nexus/internal/types"
)

func TestIntersector_Intersect(t *testing.T) {
	g := graph.NewGraph()
	g.AddNode(&types.GraphNode{ID: "A"})
	g.AddNode(&types.GraphNode{ID: "B"})
	g.AddNode(&types.GraphNode{ID: "C"})
	g.AddNode(&types.GraphNode{ID: "D"})

	// Setup graph: A-C, B-C, A-D
	g.AddEdge(types.GraphEdge{SourceID: "A", TargetID: "C"})
	g.AddEdge(types.GraphEdge{SourceID: "B", TargetID: "C"})
	g.AddEdge(types.GraphEdge{SourceID: "A", TargetID: "D"})

	intersector := NewIntersector(g)

	// Test: Intersection of A and B should be C
	res, err := intersector.Intersect(context.Background(), "A", "B")
	if err != nil {
		t.Fatalf("Intersect failed: %v", err)
	}

	if len(res) != 1 || res[0] != "C" {
		t.Errorf("Expected [C], got %v", res)
	}

	// Test: No intersection
	res, err = intersector.Intersect(context.Background(), "B", "D")
	if err != nil {
		t.Fatalf("Intersect failed: %v", err)
	}
	if len(res) != 0 {
		t.Errorf("Expected empty result, got %v", res)
	}
}

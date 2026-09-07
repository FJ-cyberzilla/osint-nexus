package engine

import (
	"context"
	"github.com/FJ-cyberzilla/osint-nexus/internal/graph"
)

// Intersector analyzes overlapping data between entities.
type Intersector struct {
	graph *graph.Graph
}

// NewIntersector initializes a new Intersector.
func NewIntersector(g *graph.Graph) *Intersector {
	return &Intersector{graph: g}
}

// Intersect finds common neighbors between two entities.
func (i *Intersector) Intersect(ctx context.Context, entityA, entityB string) ([]string, error) {
	neighborsA := i.getNeighbors(entityA)
	neighborsB := i.getNeighbors(entityB)

	intersection := []string{}
	set := make(map[string]bool)
	for _, n := range neighborsA {
		set[n] = true
	}
	for _, n := range neighborsB {
		if set[n] {
			intersection = append(intersection, n)
		}
	}
	return intersection, nil
}

func (i *Intersector) getNeighbors(entityID string) []string {
	edges := i.graph.GetEdges()
	var neighbors []string
	for _, edge := range edges {
		if edge.SourceID == entityID {
			neighbors = append(neighbors, edge.TargetID)
		} else if edge.TargetID == entityID {
			neighbors = append(neighbors, edge.SourceID)
		}
	}
	return neighbors
}

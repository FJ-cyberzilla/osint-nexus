package engine

import (
	"context"
	"github.com/FJ-cyberzilla/osint-nexus/internal/graph"
)

// Pivoter handles entity relationship traversal.
type Pivoter struct {
	graph *graph.Graph
}

// NewPivoter initializes a new Pivoter.
func NewPivoter(g *graph.Graph) *Pivoter {
	return &Pivoter{graph: g}
}

// Pivot finds related entities based on current node.
func (p *Pivoter) Pivot(ctx context.Context, nodeID string) ([]string, error) {
	edges := p.graph.GetEdges()
	var related []string
	for _, edge := range edges {
		if edge.SourceID == nodeID {
			related = append(related, edge.TargetID)
		} else if edge.TargetID == nodeID {
			related = append(related, edge.SourceID)
		}
	}
	return related, nil
}

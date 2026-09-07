package engine

import (
	"context"
	"github.com/FJ-cyberzilla/osint-nexus/internal/graph"
)

// Matcher orchestrates analysis to find paths between entities.
type Matcher struct {
	graph       *graph.Graph
	pivoter     *Pivoter
	intersector *Intersector
}

// NewMatcher initializes a new Matcher.
func NewMatcher(g *graph.Graph) *Matcher {
	return &Matcher{
		graph:       g,
		pivoter:     NewPivoter(g),
		intersector: NewIntersector(g),
	}
}

// FindPath attempts to find a connection path between two entities.
func (m *Matcher) FindPath(ctx context.Context, startNode, endNode string) ([]string, error) {
	// Simple BFS path finding
	queue := [][]string{{startNode}}
	visited := map[string]bool{startNode: true}

	for len(queue) > 0 {
		path := queue[0]
		queue = queue[1:]
		lastNode := path[len(path)-1]

		if lastNode == endNode {
			return path, nil
		}

		neighbors, _ := m.pivoter.Pivot(ctx, lastNode)
		for _, neighbor := range neighbors {
			if !visited[neighbor] {
				visited[neighbor] = true
				newPath := append([]string{}, path...)
				newPath = append(newPath, neighbor)
				queue = append(queue, newPath)
			}
		}
	}

	return nil, nil // No path found
}

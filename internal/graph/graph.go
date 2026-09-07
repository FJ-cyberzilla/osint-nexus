package graph

import (
	"fmt"
	"sync"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// Graph manages the relationship between entities.
type Graph struct {
	mu    sync.RWMutex
	nodes map[string]*types.GraphNode
	edges []types.GraphEdge
}

// NewGraph initializes and returns a new Graph.
func NewGraph() *Graph {
	return &Graph{
		nodes: make(map[string]*types.GraphNode),
		edges: make([]types.GraphEdge, 0),
	}
}

// AddNode adds a new node to the graph.
func (g *Graph) AddNode(node *types.GraphNode) error {
	g.mu.Lock()
	defer g.mu.Unlock()

	if _, exists := g.nodes[node.ID]; exists {
		return fmt.Errorf("graph: node with ID %s already exists", node.ID)
	}

	g.nodes[node.ID] = node
	return nil
}

// AddEdge adds a new relationship between two nodes.
func (g *Graph) AddEdge(edge types.GraphEdge) error {
	g.mu.Lock()
	defer g.mu.Unlock()

	if _, exists := g.nodes[edge.SourceID]; !exists {
		return fmt.Errorf("graph: source node %s not found", edge.SourceID)
	}
	if _, exists := g.nodes[edge.TargetID]; !exists {
		return fmt.Errorf("graph: target node %s not found", edge.TargetID)
	}

	g.edges = append(g.edges, edge)
	return nil
}

// GetNodes returns all nodes in the graph.
func (g *Graph) GetNodes() []*types.GraphNode {
	g.mu.RLock()
	defer g.mu.RUnlock()

	nodes := make([]*types.GraphNode, 0, len(g.nodes))
	for _, node := range g.nodes {
		nodes = append(nodes, node)
	}
	return nodes
}

// GetEdges returns all edges in the graph.
func (g *Graph) GetEdges() []types.GraphEdge {
	g.mu.RLock()
	defer g.mu.RUnlock()

	edges := make([]types.GraphEdge, len(g.edges))
	copy(edges, g.edges)
	return edges
}

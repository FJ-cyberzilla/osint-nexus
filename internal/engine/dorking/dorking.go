package dorking

import (
	"fmt"
)

// Dorker defines the contract for generating search queries.
type Dorker interface {
	Generate(target string, context string) (string, error)
}

// SimpleDorker generates search queries based on target and context.
type SimpleDorker struct {
	baseQuery string
}

// NewSimpleDorker initializes a SimpleDorker.
func NewSimpleDorker(baseQuery string) *SimpleDorker {
	return &SimpleDorker{baseQuery: baseQuery}
}

// Generate creates a search query.
func (d *SimpleDorker) Generate(target string, context string) (string, error) {
	if target == "" || context == "" {
		return "", fmt.Errorf("dorking: empty target or context")
	}
	return fmt.Sprintf("%s site:%s", context, target), nil
}

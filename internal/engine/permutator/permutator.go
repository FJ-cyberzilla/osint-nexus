package permutator

import (
	"fmt"

	"github.com/rotisserie/eris"
)

// Permutator defines the contract for generating target variants.
type Permutator interface {
	Permute(target string) ([]string, error)
}

// SimplePermutator generates basic domain permutations.
type SimplePermutator struct {
	suffixes []string
}

// NewSimplePermutator initializes a SimplePermutator.
func NewSimplePermutator(suffixes []string) *SimplePermutator {
	return &SimplePermutator{suffixes: suffixes}
}

// Permute generates variations.
func (p *SimplePermutator) Permute(target string) ([]string, error) {
	if target == "" {
		return nil, eris.New("permutator: empty target")
	}
	var results []string
	for _, suffix := range p.suffixes {
		results = append(results, fmt.Sprintf("%s%s", target, suffix))
	}
	return results, nil
}

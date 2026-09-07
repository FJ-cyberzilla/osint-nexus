package extractor

import (
	"context"
	"fmt"
	"strings"

	"github.com/osint-nexus/internal/types"
	"golang.org/x/net/html"
)

// StreamHandler defines the contract for extractors that can process tokens
// in a single streaming pass.
type StreamHandler interface {
	HandleToken(token html.Token)
	HandleText(text string)
	GetPivots() *types.ExtractedPivots
}

// Orchestrator coordinates multiple extractors to harvest pivots.
type Orchestrator struct {
	extractors []types.Extractor
	handlers   []StreamHandler
}

// NewOrchestrator creates a new orchestrator with the provided extractors.
func NewOrchestrator(extractors ...types.Extractor) *Orchestrator {
	var handlers []StreamHandler
	for _, e := range extractors {
		if h, ok := e.(StreamHandler); ok {
			handlers = append(handlers, h)
		}
	}
	return &Orchestrator{extractors: extractors, handlers: handlers}
}

// Extract runs all registered extractors and aggregates the results.
func (o *Orchestrator) Extract(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	if len(o.handlers) == len(o.extractors) {
		return o.extractStreaming(ctx, rawHTML)
	}
	
	// Fallback to legacy extraction if not all extractors support streaming
	result := &types.ExtractedPivots{
		Emails:        []string{},
		PGPKeys:       []string{},
		ExternalLinks: []string{},
		SocialHandles: []types.SocialHandle{},
	}

	for _, e := range o.extractors {
		pivots, err := e.Extract(ctx, rawHTML)
		if err != nil {
			return nil, fmt.Errorf("extractor_orchestrator: %w", err)
		}

		if pivots.Emails != nil {
			result.Emails = append(result.Emails, pivots.Emails...)
		}
		if pivots.PGPKeys != nil {
			result.PGPKeys = append(result.PGPKeys, pivots.PGPKeys...)
		}
		if pivots.ExternalLinks != nil {
			result.ExternalLinks = append(result.ExternalLinks, pivots.ExternalLinks...)
		}
		if pivots.SocialHandles != nil {
			result.SocialHandles = append(result.SocialHandles, pivots.SocialHandles...)
		}
		if pivots.Bio != nil && *pivots.Bio != "" {
			result.Bio = pivots.Bio
		}
	}

	return result, nil
}

func (o *Orchestrator) extractStreaming(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	tokenizer := html.NewTokenizer(strings.NewReader(rawHTML))
	
	for {
		tokenType := tokenizer.Next()
		if tokenType == html.ErrorToken {
			break
		}

		token := tokenizer.Token()
		
		if tokenType == html.TextToken {
			text := token.Data
			for _, h := range o.handlers {
				h.HandleText(text)
			}
		} else {
			for _, h := range o.handlers {
				h.HandleToken(token)
			}
		}
	}

	result := &types.ExtractedPivots{
		Emails:        []string{},
		PGPKeys:       []string{},
		ExternalLinks: []string{},
		SocialHandles: []types.SocialHandle{},
	}

	for _, h := range o.handlers {
		pivots := h.GetPivots()
		if pivots.Emails != nil {
			result.Emails = append(result.Emails, pivots.Emails...)
		}
		if pivots.PGPKeys != nil {
			result.PGPKeys = append(result.PGPKeys, pivots.PGPKeys...)
		}
		if pivots.ExternalLinks != nil {
			result.ExternalLinks = append(result.ExternalLinks, pivots.ExternalLinks...)
		}
		if pivots.SocialHandles != nil {
			result.SocialHandles = append(result.SocialHandles, pivots.SocialHandles...)
		}
		if pivots.Bio != nil && *pivots.Bio != "" {
			result.Bio = pivots.Bio
		}
	}

	return result, nil
}

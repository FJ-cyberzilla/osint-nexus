package extractor

import (
	"context"
	"strings"

	"github.com/osint-nexus/internal/types"
	"golang.org/x/net/html"
)

// MetaExtractor handles meta tag and bio harvesting using a streaming tokenizer.
type MetaExtractor struct{}

// NewMetaExtractor initializes a new MetaExtractor.
func NewMetaExtractor() *MetaExtractor {
	return &MetaExtractor{}
}

// Extract implements the Extractor interface for meta tag/bio harvesting.
func (m *MetaExtractor) Extract(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	tokenizer := html.NewTokenizer(strings.NewReader(rawHTML))
	var bio string

	for {
		tokenType := tokenizer.Next()
		if tokenType == html.ErrorToken {
			break
		}

		if tokenType == html.SelfClosingTagToken || tokenType == html.StartTagToken {
			token := tokenizer.Token()
			if token.Data == "meta" {
				var name, content string
				for _, attr := range token.Attr {
					if attr.Key == "name" || attr.Key == "property" {
						name = attr.Val
					} else if attr.Key == "content" {
						content = attr.Val
					}
				}

				if (name == "description" || name == "og:description" || name == "twitter:description") && content != "" {
					bio = content
					break // Found a suitable description
				}
			}
		}
	}

	return &types.ExtractedPivots{Bio: &bio}, nil
}

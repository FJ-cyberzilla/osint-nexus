package extractor

import (
	"context"
	"net/url"
	"strings"

	"github.com/osint-nexus/internal/types"
	"golang.org/x/net/html"
)

// SocialExtractor harvests links and identifies social media handles
// using a streaming tokenizer and provided configuration.
type SocialExtractor struct {
	config *types.Config
}

// NewSocialExtractor initializes a new SocialExtractor with the provided config.
func NewSocialExtractor(cfg *types.Config) *SocialExtractor {
	return &SocialExtractor{config: cfg}
}

// Extract implements the Extractor interface for link/social handle harvesting.
func (s *SocialExtractor) Extract(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	tokenizer := html.NewTokenizer(strings.NewReader(rawHTML))
	linkSet := make(map[string]struct{})
	var socialHandles []types.SocialHandle

	for {
		tokenType := tokenizer.Next()
		if tokenType == html.ErrorToken {
			break
		}

		if (tokenType == html.StartTagToken || tokenType == html.SelfClosingTagToken) {
			token := tokenizer.Token()
			if token.Data == "a" {
				for _, attr := range token.Attr {
					if attr.Key == "href" {
						href := attr.Val
						if !strings.HasPrefix(href, "http://") && !strings.HasPrefix(href, "https://") {
							continue
						}

						parsed, err := url.Parse(href)
						if err != nil {
							continue
						}

						linkSet[href] = struct{}{}

						platform, username := s.identifySocial(strings.ToLower(parsed.Host), parsed.Path)
						if platform != "" {
							socialHandles = append(socialHandles, types.SocialHandle{
								Platform: platform,
								Username: username,
								URL:      href,
							})
						}
					}
				}
			}
		}
	}

	links := make([]string, 0, len(linkSet))
	for link := range linkSet {
		links = append(links, link)
	}

	return &types.ExtractedPivots{ExternalLinks: links, SocialHandles: socialHandles}, nil
}

func (s *SocialExtractor) identifySocial(domain, path string) (string, string) {
	platform, found := s.config.PlatformMap[domain]
	if !found {
		for d, name := range s.config.PlatformMap {
			if strings.HasSuffix(domain, "."+d) {
				platform = name
				break
			}
		}
	}

	if platform == "" {
		return "", ""
	}

	trimmedPath := strings.Trim(path, "/")
	if trimmedPath == "" {
		return "", ""
	}

	idx := strings.IndexByte(trimmedPath, '/')
	username := trimmedPath
	if idx != -1 {
		username = trimmedPath[:idx]
	}

	if s.config.IgnoredHandles[username] {
		return "", ""
	}

	return platform, username
}

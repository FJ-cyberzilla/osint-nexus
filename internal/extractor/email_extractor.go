package extractor

import (
	"context"
	"fmt"
	"regexp"
	"strings"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"golang.org/x/net/html"
)

// EmailExtractor handles email address harvesting via regex.
type EmailExtractor struct {
	emailRegex *regexp.Regexp
	emails     map[string]struct{}
}

// NewEmailExtractor initializes and returns a configured EmailExtractor.
func NewEmailExtractor() (*EmailExtractor, error) {
	pattern, err := regexp.Compile(`(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}`)
	if err != nil {
		return nil, fmt.Errorf("email_extractor: compile regex: %w", err)
	}

	return &EmailExtractor{
		emailRegex: pattern,
		emails:     make(map[string]struct{}),
	}, nil
}

// Extract implements the Extractor interface for email harvesting.
func (e *EmailExtractor) Extract(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	// Reset internal state for non-streaming use
	e.reset()

	matches := e.emailRegex.FindAllString(rawHTML, -1)
	for _, m := range matches {
		e.emails[m] = struct{}{}
	}

	return e.GetPivots(), nil
}

func (e *EmailExtractor) HandleToken(token html.Token) {
	for _, attr := range token.Attr {
		if attr.Key == "href" {
			if strings.HasPrefix(attr.Val, "mailto:") {
				email := strings.TrimPrefix(attr.Val, "mailto:")
				if e.emailRegex.MatchString(email) {
					e.emails[email] = struct{}{}
				}
			}
		}
	}
}

func (e *EmailExtractor) HandleText(text string) {
	matches := e.emailRegex.FindAllString(text, -1)
	for _, m := range matches {
		e.emails[m] = struct{}{}
	}
}

func (e *EmailExtractor) GetPivots() *types.ExtractedPivots {
	emails := make([]string, 0, len(e.emails))
	for email := range e.emails {
		emails = append(emails, email)
	}
	// Note: We don't clear the map here to allow Orchestrator 
	// to aggregate multiple extractors if needed, 
	// though the current Orchestrator clears state per Extract.
	return &types.ExtractedPivots{Emails: emails}
}

func (e *EmailExtractor) reset() {
	for k := range e.emails {
		delete(e.emails, k)
	}
}

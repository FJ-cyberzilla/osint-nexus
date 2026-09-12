package extractor

import (
	"context"
	"fmt"
	"regexp"
	"strings"
	"sync"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"golang.org/x/net/html"
)

// EmailExtractor handles email address harvesting via regex.
type EmailExtractor struct {
	emailRegex *regexp.Regexp
	emails     map[string]struct{}
	pool       sync.Pool
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
		pool: sync.Pool{
			New: func() any {
				return make(map[string]struct{})
			},
		},
	}, nil
}

// Extract implements the Extractor interface for email harvesting.
func (e *EmailExtractor) Extract(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	emailSet := e.pool.Get().(map[string]struct{})
	defer func() {
		// Clear map before returning to pool
		for k := range emailSet {
			delete(emailSet, k)
		}
		e.pool.Put(emailSet)
	}()

	matches := e.emailRegex.FindAllString(rawHTML, -1)
	for _, m := range matches {
		emailSet[m] = struct{}{}
	}

	emails := make([]string, 0, len(emailSet))
	for email := range emailSet {
		emails = append(emails, email)
	}

	return &types.ExtractedPivots{Emails: emails}, nil
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
	return &types.ExtractedPivots{Emails: emails}
}

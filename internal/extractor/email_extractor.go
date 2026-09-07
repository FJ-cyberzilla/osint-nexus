package extractor

import (
	"context"
	"fmt"
	"regexp"
	"strings"

	"github.com/osint-nexus/internal/types"
	"golang.org/x/net/html"
)

// EmailExtractor handles email address harvesting via regex.
type EmailExtractor struct {
	emailRegex *regexp.Regexp
	emails     map[string]struct{}
}

// NewEmailExtractor initializes and returns a configured EmailExtractor.
func NewEmailExtractor() (*EmailExtractor, error) {
	// Reusing the compiled regex pattern from the previous implementation.
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
	matches := e.emailRegex.FindAllString(rawHTML, -1)
	
	emailSet := make(map[string]struct{}, len(matches))
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
	// Look for emails in href attributes
	for _, attr := range token.Attr {
		if attr.Key == "href" {
			// Extract email if href starts with mailto:
			if strings.HasPrefix(attr.Val, "mailto:") {
				email := strings.TrimPrefix(attr.Val, "mailto:")
				// Basic validation
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

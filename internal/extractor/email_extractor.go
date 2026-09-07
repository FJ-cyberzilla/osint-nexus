package extractor

import (
	"context"
	"fmt"
	"regexp"

	"github.com/osint-nexus/internal/types"
)

// EmailExtractor handles email address harvesting via regex.
type EmailExtractor struct {
	emailRegex *regexp.Regexp
}

// NewEmailExtractor initializes and returns a configured EmailExtractor.
func NewEmailExtractor() (*EmailExtractor, error) {
	// Reusing the compiled regex pattern from the previous implementation.
	pattern, err := regexp.Compile(`(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}`)
	if err != nil {
		return nil, fmt.Errorf("email_extractor: compile regex: %w", err)
	}
	return &EmailExtractor{emailRegex: pattern}, nil
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

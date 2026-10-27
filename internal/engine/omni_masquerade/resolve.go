package omni_masquerade

import (
	"strings"
)

// EntityResolver canonicalizes handles, usernames, and pivot addresses to ensure deterministic entity mapping.
type EntityResolver struct{}

// NewEntityResolver initializes a new EntityResolver.
func NewEntityResolver() *EntityResolver {
	return &EntityResolver{}
}

// CanonicalizeUsername standardizes username formatting (lowercasing, trimming whitespace, stripping invalid symbols).
func (er *EntityResolver) CanonicalizeUsername(username string) string {
	cleaned := strings.TrimSpace(username)
	cleaned = strings.ToLower(cleaned)
	cleaned = strings.TrimPrefix(cleaned, "@")
	return cleaned
}

// DeduplicateStrings removes duplicate entries from a slice of strings while preserving relative order.
func (er *EntityResolver) DeduplicateStrings(items []string) []string {
	seen := make(map[string]bool)
	var result []string
	for _, item := range items {
		trimmed := strings.TrimSpace(item)
		if trimmed != "" && !seen[trimmed] {
			seen[trimmed] = true
			result = append(result, trimmed)
		}
	}
	return result
}

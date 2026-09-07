package types

import (
	"context"
)

// Extractor defines the contract for harvesting specific pivot types
// from raw HTML or processed document structures.
type Extractor interface {
	Extract(ctx context.Context, rawHTML string) (*ExtractedPivots, error)
}

// Config defines the configuration for extractors,
// replacing hardcoded package-level globals.
type Config struct {
	PlatformMap    map[string]string
	IgnoredHandles map[string]bool
}

// NewDefaultConfig returns a configuration with the current project defaults.
func NewDefaultConfig() *Config {
	return &Config{
		PlatformMap: map[string]string{
			"twitter.com":   "Twitter",
			"x.com":         "Twitter",
			"instagram.com": "Instagram",
			"linkedin.com":  "LinkedIn",
			"github.com":    "GitHub",
			"t.me":          "Telegram",
		},
		IgnoredHandles: map[string]bool{
			"share":  true,
			"home":   true,
			"intent": true,
			"search": true,
			"p":      true,
		},
	}
}

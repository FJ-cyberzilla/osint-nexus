package extractor

import (
	"context"
	"testing"
)

func TestPivotExtractor_Extract(t *testing.T) {
	extractor, err := NewPivotExtractor()
	if err != nil {
		t.Fatalf("Failed to create extractor: %v", err)
	}

	rawHTML := `
<html>
<head>
    <meta name="description" content="Test Bio">
</head>
<body>
    <a href="mailto:test@example.com">Email</a>
    <a href="https://github.com/testuser">GitHub</a>
    <a href="https://t.me/telegramuser">Telegram</a>
    <pre>
-----BEGIN PGP PUBLIC KEY BLOCK-----
Key data
-----END PGP PUBLIC KEY BLOCK-----
    </pre>
</body>
</html>
`
	ctx := context.Background()
	pivots, err := extractor.Extract(ctx, rawHTML, "https://example.com")
	if err != nil {
		t.Fatalf("Extract failed: %v", err)
	}

	if len(pivots.Emails) != 1 || pivots.Emails[0] != "test@example.com" {
		t.Errorf("Expected test@example.com, got %v", pivots.Emails)
	}

	if len(pivots.PGPKeys) != 1 {
		t.Errorf("Expected 1 PGP key, got %d", len(pivots.PGPKeys))
	}

	// Expecting 2: GitHub and Telegram
	if len(pivots.SocialHandles) != 2 {
		t.Errorf("Expected 2 social handles, got %d", len(pivots.SocialHandles))
	}

	foundGitHub := false
	foundTelegram := false
	for _, h := range pivots.SocialHandles {
		if h.Platform == "GitHub" && h.Username == "testuser" {
			foundGitHub = true
		}
		if h.Platform == "Telegram" && h.Username == "telegramuser" {
			foundTelegram = true
		}
	}
	if !foundGitHub || !foundTelegram {
		t.Errorf("Missing handles. GitHub: %v, Telegram: %v", foundGitHub, foundTelegram)
	}

	if *pivots.Bio != "Test Bio" {
		t.Errorf("Expected 'Test Bio', got '%s'", *pivots.Bio)
	}
}

package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// GoogleChatProvider probes Google Chat profile/space existence.
type GoogleChatProvider struct {
	client *http.Client
}

func NewGoogleChatProvider() *GoogleChatProvider {
	return &GoogleChatProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewGoogleChatProvider())
}

func (p *GoogleChatProvider) Name() string {
	return "GoogleChat"
}

func (p *GoogleChatProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://chat.google.com/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "googlechat: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "googlechat: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "GoogleChat"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.85,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("googlechat: rate limit exceeded")
	}
	return nil, nil
}

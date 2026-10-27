package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// AnonChatProvider probes anonymous chat profile/user existence.
type AnonChatProvider struct {
	client *http.Client
}

func NewAnonChatProvider() *AnonChatProvider {
	return &AnonChatProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewAnonChatProvider())
}

func (p *AnonChatProvider) Name() string {
	return "AnonChat"
}

func (p *AnonChatProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://anonymous-chat.org/u/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "anonchat: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "anonchat: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "AnonChat"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.8,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("anonchat: rate limit exceeded")
	}
	return nil, nil
}

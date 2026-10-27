package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// DiscordProvider probes Discord profile existence.
type DiscordProvider struct {
	client *http.Client
}

// NewDiscordProvider initializes a new DiscordProvider.
func NewDiscordProvider() *DiscordProvider {
	return &DiscordProvider{
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func init() {
	Register(NewDiscordProvider())
}

// Name returns the provider name.
func (p *DiscordProvider) Name() string {
	return "Discord"
}

// CheckUsername checks if a username exists on Discord.
func (p *DiscordProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://discord.com/users/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "discord: create request")
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OSINT-Nexus/1.0")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "discord: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusUnauthorized {
		platform := "Discord"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{
				{
					Username: &username,
					Platform: &platform,
				},
			},
			ConfidenceScore: 0.85,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("discord: rate limit exceeded")
	}

	return nil, nil
}

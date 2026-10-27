package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	TwitchBaseURL      = "https://www.twitch.tv"
	TwitchConfidence   = 0.9
	TwitchPlatformName = "Twitch"
	TwitchAccountID    = "twitch-detected"
)

// TwitchProvider probes Twitch profiles.
type TwitchProvider struct {
	client *http.Client
}

// NewTwitchProvider initializes a new TwitchProvider.
func NewTwitchProvider() *TwitchProvider {
	return &TwitchProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewTwitchProvider())
}

// Name returns the provider name.
func (p *TwitchProvider) Name() string {
	return TwitchPlatformName
}

// CheckUsername probes Twitch for the username.
func (p *TwitchProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s/%s", TwitchBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "twitch: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("twitch: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := TwitchPlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       TwitchAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: TwitchConfidence,
	}, nil
}

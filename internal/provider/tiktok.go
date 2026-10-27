package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	TikTokBaseURL      = "https://www.tiktok.com/@"
	TikTokConfidence   = 0.9
	TikTokPlatformName = "TikTok"
	TikTokAccountID    = "tiktok-detected"
)

// TikTokProvider probes TikTok profiles.
type TikTokProvider struct {
	client *http.Client
}

// NewTikTokProvider initializes a new TikTokProvider.
func NewTikTokProvider() *TikTokProvider {
	return &TikTokProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewTikTokProvider())
}

// Name returns the provider name.
func (p *TikTokProvider) Name() string {
	return TikTokPlatformName
}

// CheckUsername probes TikTok for the username.
func (p *TikTokProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s%s", TikTokBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "tiktok: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("tiktok: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := TikTokPlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       TikTokAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: TikTokConfidence,
	}, nil
}

package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// SpotifyProvider probes Spotify profile existence.
type SpotifyProvider struct {
	client *http.Client
}

func NewSpotifyProvider() *SpotifyProvider {
	return &SpotifyProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewSpotifyProvider())
}

func (p *SpotifyProvider) Name() string {
	return "Spotify"
}

func (p *SpotifyProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://open.spotify.com/user/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "spotify: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "spotify: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Spotify"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.85,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("spotify: rate limit exceeded")
	}
	return nil, nil
}

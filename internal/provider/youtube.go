package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	YouTubeBaseURL      = "https://www.youtube.com/@"
	YouTubeConfidence   = 0.9
	YouTubePlatformName = "YouTube"
	YouTubeAccountID    = "youtube-detected"
)

// YouTubeProvider probes YouTube profiles.
type YouTubeProvider struct {
	client *http.Client
}

// NewYouTubeProvider initializes a new YouTubeProvider.
func NewYouTubeProvider() *YouTubeProvider {
	return &YouTubeProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewYouTubeProvider())
}

// Name returns the provider name.
func (p *YouTubeProvider) Name() string {
	return YouTubePlatformName
}

// CheckUsername probes YouTube for the username.
func (p *YouTubeProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s%s", YouTubeBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "youtube: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("youtube: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := YouTubePlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       YouTubeAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: YouTubeConfidence,
	}, nil
}

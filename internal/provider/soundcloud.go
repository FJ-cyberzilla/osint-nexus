package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	SoundCloudBaseURL      = "https://soundcloud.com"
	SoundCloudConfidence   = 0.9
	SoundCloudPlatformName = "SoundCloud"
	SoundCloudAccountID    = "soundcloud-detected"
)

// SoundCloudProvider probes SoundCloud profiles.
type SoundCloudProvider struct {
	client *http.Client
}

// NewSoundCloudProvider initializes a new SoundCloudProvider.
func NewSoundCloudProvider() *SoundCloudProvider {
	return &SoundCloudProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewSoundCloudProvider())
}

// Name returns the provider name.
func (p *SoundCloudProvider) Name() string {
	return SoundCloudPlatformName
}

// CheckUsername probes SoundCloud for the username.
func (p *SoundCloudProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s/%s", SoundCloudBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "soundcloud: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("soundcloud: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := SoundCloudPlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       SoundCloudAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: SoundCloudConfidence,
	}, nil
}

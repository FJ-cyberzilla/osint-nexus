package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	MediumBaseURL      = "https://medium.com/@"
	MediumConfidence   = 0.9
	MediumPlatformName = "Medium"
	MediumAccountID    = "medium-detected"
)

// MediumProvider probes Medium profiles.
type MediumProvider struct {
	client *http.Client
}

// NewMediumProvider initializes a new MediumProvider.
func NewMediumProvider() *MediumProvider {
	return &MediumProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewMediumProvider())
}

// Name returns the provider name.
func (p *MediumProvider) Name() string {
	return MediumPlatformName
}

// CheckUsername probes Medium for the username.
func (p *MediumProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s%s", MediumBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "medium: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("medium: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := MediumPlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       MediumAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: MediumConfidence,
	}, nil
}

package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// ClubhouseProvider probes Clubhouse profile existence.
type ClubhouseProvider struct {
	client *http.Client
}

func NewClubhouseProvider() *ClubhouseProvider {
	return &ClubhouseProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewClubhouseProvider())
}

func (p *ClubhouseProvider) Name() string {
	return "Clubhouse"
}

func (p *ClubhouseProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://www.clubhouse.com/@%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "clubhouse: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "clubhouse: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Clubhouse"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("clubhouse: rate limit exceeded")
	}
	return nil, nil
}

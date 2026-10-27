package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// ZoomProvider probes Zoom profile existence.
type ZoomProvider struct {
	client *http.Client
}

func NewZoomProvider() *ZoomProvider {
	return &ZoomProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewZoomProvider())
}

func (p *ZoomProvider) Name() string {
	return "Zoom"
}

func (p *ZoomProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://zoom.us/u/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "zoom: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "zoom: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Zoom"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.8,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("zoom: rate limit exceeded")
	}
	return nil, nil
}

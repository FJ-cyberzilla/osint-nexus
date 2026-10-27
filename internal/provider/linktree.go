package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// LinktreeProvider probes Linktree profile existence.
type LinktreeProvider struct {
	client *http.Client
}

func NewLinktreeProvider() *LinktreeProvider {
	return &LinktreeProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewLinktreeProvider())
}

func (p *LinktreeProvider) Name() string {
	return "Linktree"
}

func (p *LinktreeProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://linktr.ee/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "linktree: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "linktree: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Linktree"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.95,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("linktree: rate limit exceeded")
	}
	return nil, nil
}

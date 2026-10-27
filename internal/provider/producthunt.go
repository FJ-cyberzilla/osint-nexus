package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// ProductHuntProvider probes Product Hunt profile existence.
type ProductHuntProvider struct {
	client *http.Client
}

func NewProductHuntProvider() *ProductHuntProvider {
	return &ProductHuntProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewProductHuntProvider())
}

func (p *ProductHuntProvider) Name() string {
	return "ProductHunt"
}

func (p *ProductHuntProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://www.producthunt.com/@%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "producthunt: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "producthunt: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "ProductHunt"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("producthunt: rate limit exceeded")
	}
	return nil, nil
}

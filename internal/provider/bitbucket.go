package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// BitbucketProvider probes Bitbucket profile existence.
type BitbucketProvider struct {
	client *http.Client
}

// NewBitbucketProvider initializes BitbucketProvider.
func NewBitbucketProvider() *BitbucketProvider {
	return &BitbucketProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewBitbucketProvider())
}

func (p *BitbucketProvider) Name() string {
	return "Bitbucket"
}

func (p *BitbucketProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://bitbucket.org/%s/", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "bitbucket: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "bitbucket: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Bitbucket"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("bitbucket: rate limit exceeded")
	}
	return nil, nil
}

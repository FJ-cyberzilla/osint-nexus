package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	TelegramBaseURL      = "https://t.me"
	TelegramConfidence   = 0.9
	TelegramPlatformName = "Telegram"
	TelegramAccountID    = "telegram-detected"
)

// TelegramProvider probes Telegram profiles/channels.
type TelegramProvider struct {
	client *http.Client
}

// NewTelegramProvider initializes a new TelegramProvider.
func NewTelegramProvider() *TelegramProvider {
	return &TelegramProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewTelegramProvider())
}

// Name returns the provider name.
func (p *TelegramProvider) Name() string {
	return TelegramPlatformName
}

// CheckUsername probes Telegram for the username.
func (p *TelegramProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s/%s", TelegramBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "telegram: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("telegram: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := TelegramPlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       TelegramAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: TelegramConfidence,
	}, nil
}

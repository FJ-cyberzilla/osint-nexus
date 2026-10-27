package omni_masquerade

import (
	"sync"
	"time"

	"github.com/rotisserie/eris"
)

// AuthToken represents a target platform token or cookie set.
type AuthToken struct {
	Platform  string    `json:"platform"`
	Token     string    `json:"token"`
	Cookie    string    `json:"cookie"`
	ExpiresAt time.Time `json:"expires_at"`
}

// TokenVault provides thread-safe in-memory rotation of platform cookies and authentication tokens.
type TokenVault struct {
	mu     sync.RWMutex
	tokens map[string][]AuthToken
	active map[string]int
}

// NewTokenVault initializes a new TokenVault.
func NewTokenVault() *TokenVault {
	return &TokenVault{
		tokens: make(map[string][]AuthToken),
		active: make(map[string]int),
	}
}

// AddToken registers an authentication token or cookie set for a platform.
func (v *TokenVault) AddToken(platform string, token AuthToken) {
	v.mu.Lock()
	defer v.mu.Unlock()
	v.tokens[platform] = append(v.tokens[platform], token)
}

// RotateToken advances to the next available valid token for the platform without dropping session.
func (v *TokenVault) RotateToken(platform string) (AuthToken, error) {
	v.mu.Lock()
	defer v.mu.Unlock()

	list, exists := v.tokens[platform]
	if !exists || len(list) == 0 {
		return AuthToken{}, eris.Errorf("token_vault: no tokens available for platform %s", platform)
	}

	currentIndex := v.active[platform]
	nextIndex := (currentIndex + 1) % len(list)
	v.active[platform] = nextIndex

	activeToken := list[nextIndex]
	if !activeToken.ExpiresAt.IsZero() && time.Now().After(activeToken.ExpiresAt) {
		return AuthToken{}, eris.Errorf("token_vault: token for %s is expired", platform)
	}

	return activeToken, nil
}

// GetActiveToken retrieves the currently selected token for the platform.
func (v *TokenVault) GetActiveToken(platform string) (AuthToken, error) {
	v.mu.RLock()
	defer v.mu.RUnlock()

	list, exists := v.tokens[platform]
	if !exists || len(list) == 0 {
		return AuthToken{}, eris.Errorf("token_vault: no tokens available for platform %s", platform)
	}

	index := v.active[platform]
	if index >= len(list) {
		index = 0
	}
	return list[index], nil
}

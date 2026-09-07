package provider

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"

	"github.com/FJ-cyberzilla/osint-nexus/internal/config"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const FingerbankDefaultBaseURL = "https://api.fingerbank.org/api/v2"

// FingerbankClient handles communication with Fingerbank API.
type FingerbankClient struct {
	client  *http.Client
	apiKey  string
	baseURL string
	enabled bool
}

// NewFingerbankClient initializes a new FingerbankClient using config.
func NewFingerbankClient() (*FingerbankClient, error) {
	cfg, err := config.Get()
	if err != nil {
		return nil, eris.Wrap(err, "fingerbank: failed to get config")
	}
	// In production, the API key should be loaded from a secure env var or secret manager.
	// For now, we look for it in OSINT_FINGERBANK_API_KEY env var.
	apiKey := os.Getenv("OSINT_FINGERBANK_API_KEY")

	enabled := cfg.Provider.Fingerbank.Enabled && apiKey != ""

	return &FingerbankClient{
		client:  NewHTTPClient(),
		apiKey:  apiKey,
		baseURL: FingerbankDefaultBaseURL,
		enabled: enabled,
	}, nil
}

// NewFingerbankClientWithURL initializes a new FingerbankClient with custom base URL.
func NewFingerbankClientWithURL(apiKey string, baseURL string) *FingerbankClient {
	return &FingerbankClient{
		client:  NewHTTPClient(),
		apiKey:  apiKey,
		baseURL: baseURL,
		enabled: apiKey != "",
	}
}

// IsEnabled returns the current enabled status of the client.
func (p *FingerbankClient) IsEnabled() bool {
	return p.enabled
}

// Name returns the provider name.
func (p *FingerbankClient) Name() string {
	return "FingerbankClient"
}

// handleResponseError maps API status codes to meaningful errors.
func (p *FingerbankClient) handleResponseError(resp *http.Response) error {
	switch resp.StatusCode {
	case http.StatusOK:
		return nil
	case http.StatusUnauthorized:
		return eris.New("fingerbank: unauthorized: invalid or missing API key")
	case http.StatusForbidden:
		return eris.New("fingerbank: forbidden: account may be blocked")
	case http.StatusTooManyRequests:
		return eris.New("fingerbank: rate limit exceeded")
	case http.StatusBadGateway:
		return eris.New("fingerbank: API backend overloaded or in maintenance")
	case http.StatusNotFound:
		return eris.New("fingerbank: no device profiling result found")
	default:
		return eris.Errorf("fingerbank: unexpected status code: %d", resp.StatusCode)
	}
}

// executeGET is a helper to execute GET requests and decode response.
func (p *FingerbankClient) executeGET[T any](ctx context.Context, endpoint string, result *T) error {
	url := fmt.Sprintf("%s/%s?key=%s", p.baseURL, endpoint, p.apiKey)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return eris.Wrap(err, "fingerbank: create request")
	}

	resp, err := p.client.Do(req)
	if err != nil {
		return eris.Wrap(err, "fingerbank: execute request")
	}
	defer resp.Body.Close()

	if err := p.handleResponseError(resp); err != nil {
		return err
	}

	if err := json.NewDecoder(resp.Body).Decode(result); err != nil {
		return eris.Wrap(err, "fingerbank: decode response")
	}
	return nil
}

// Interrogate sends an interrogation request to Fingerbank, or returns error if disabled.
func (p *FingerbankClient) Interrogate(ctx context.Context, payload types.FingerbankPayload) (*types.FingerbankInterrogateResponse, error) {
	if !p.enabled {
		return nil, eris.New("fingerbank: provider disabled or missing API key")
	}

	url := fmt.Sprintf("%s/combinations/interrogate?key=%s", p.baseURL, p.apiKey)

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, eris.Wrap(err, "fingerbank: marshal payload")
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, eris.Wrap(err, "fingerbank: create request")
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "fingerbank: execute request")
	}
	defer resp.Body.Close()

	if err := p.handleResponseError(resp); err != nil {
		return nil, err
	}

	var result types.FingerbankInterrogateResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, eris.Wrap(err, "fingerbank: decode response")
	}

	return &result, nil
}

// GetDevice retrieves device details by ID.
func (p *FingerbankClient) GetDevice(ctx context.Context, id string) (*types.Device, error) {
	if !p.enabled {
		return nil, eris.New("fingerbank: provider disabled or missing API key")
	}
	var device types.Device
	if err := p.executeGET(ctx, fmt.Sprintf("devices/%s", id), &device); err != nil {
		return nil, err
	}
	return &device, nil
}

// GetDeviceProfilingRules retrieves profiling rules for a device.
func (p *FingerbankClient) GetDeviceProfilingRules(ctx context.Context, id string) ([]types.ProfilingRule, error) {
	if !p.enabled {
		return nil, eris.New("fingerbank: provider disabled or missing API key")
	}
	var rules []types.ProfilingRule
	if err := p.executeGET(ctx, fmt.Sprintf("devices/%s/profiling_rules", id), &rules); err != nil {
		return nil, err
	}
	return rules, nil
}

// GetDeviceVulnerabilities retrieves vulnerabilities for a device.
func (p *FingerbankClient) GetDeviceVulnerabilities(ctx context.Context, id string) ([]types.Vulnerability, error) {
	if !p.enabled {
		return nil, eris.New("fingerbank: provider disabled or missing API key")
	}
	var vulnerabilities []types.Vulnerability
	if err := p.executeGET(ctx, fmt.Sprintf("devices/%s/vulnerabilities", id), &vulnerabilities); err != nil {
		return nil, err
	}
	return vulnerabilities, nil
}

// IsDeviceA checks if a device is of a certain type/is another device.
func (p *FingerbankClient) IsDeviceA(ctx context.Context, id, otherID string) (bool, error) {
	if !p.enabled {
		return false, eris.New("fingerbank: provider disabled or missing API key")
	}
	var res types.IsAResponse
	if err := p.executeGET(ctx, fmt.Sprintf("devices/%s/is_a/%s", id, otherID), &res); err != nil {
		return false, err
	}
	return res.IsA, nil
}

// IsResultReliable checks if the confidence score meets the threshold for reliability.
func (p *FingerbankClient) IsResultReliable(score int) bool {
	return score >= 50
}

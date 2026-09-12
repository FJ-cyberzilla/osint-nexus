package network

import (
	"context"
	"net"
	"net/http"
	"time"

	"github.com/rotisserie/eris"
)

// NetworkManager implements the Intermediator interface and manages
// network operations with automatic fallback mechanisms.
type NetworkManager struct {
	dohClient  *DoHClient
	tlsProxy   *TLSProxy
	dataDrop   *DataDropService
	endpoints  *Endpoints
	httpClient *http.Client
}

// NewNetworkManager initializes a new NetworkManager with optional endpoints and a configured HTTP client.
func NewNetworkManager(ep *Endpoints) *NetworkManager {
	transport := &http.Transport{
		DialContext: (&net.Dialer{
			Timeout:   30 * time.Second,
			KeepAlive: 30 * time.Second,
		}).DialContext,
		MaxIdleConns:          100,
		MaxIdleConnsPerHost:   20,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
	}

	return &NetworkManager{
		dohClient: &DoHClient{},
		tlsProxy:  &TLSProxy{},
		dataDrop:  &DataDropService{},
		endpoints: ep,
		httpClient: &http.Client{
			Transport: transport,
			Timeout:   60 * time.Second,
		},
	}
}

// ResolveDNS attempts DoH resolution and falls back to standard DNS.
func (nm *NetworkManager) ResolveDNS(ctx context.Context, hostname string) ([]string, error) {
	// Primary: Attempt DoH
	results, err := nm.dohClient.Resolve(ctx, hostname)
	if err == nil {
		return results, nil
	}

	// Fallback: Standard DNS
	return nm.dohClient.FallbackToStandard(ctx, hostname)
}

// SecureTLSHandshake attempts an advanced TLS handshake, falling back to standard.
func (nm *NetworkManager) SecureTLSHandshake(ctx context.Context, address string) (any, error) {
	// Primary: Attempt Advanced TLS
	results, err := nm.tlsProxy.Handshake(ctx, address)
	if err == nil {
		return results, nil
	}

	// Fallback: Standard TLS
	return nm.tlsProxy.FallbackToStandard(ctx, address)
}

// OffloadData handles secure data offloading.
func (nm *NetworkManager) OffloadData(ctx context.Context, data []byte) error {
	return nm.dataDrop.Send(ctx, data)
}

// UpdateLinkedIP triggers an update for the linked IP using the configured URL.
func (nm *NetworkManager) UpdateLinkedIP(ctx context.Context) error {
	if nm.endpoints == nil || nm.endpoints.LinkIPURL == "" {
		return eris.New("network: no endpoint configuration for IP update")
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, nm.endpoints.LinkIPURL, nil)
	if err != nil {
		return eris.Wrap(err, "network: failed to create request for IP update")
	}
	resp, err := nm.httpClient.Do(req)
	if err != nil {
		return eris.Wrap(err, "network: failed to execute IP update request")
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return eris.Errorf("network: unexpected status code for IP update: %d", resp.StatusCode)
	}
	return nil
}

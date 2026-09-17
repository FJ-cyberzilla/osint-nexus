package network

import (
	"context"
	"errors"
	"reflect"
	"testing"
)

type mockResolver struct {
	resolveFunc func(ctx context.Context, hostname string) ([]string, error)
	fallbackFunc func(ctx context.Context, hostname string) ([]string, error)
}

func (m *mockResolver) Resolve(ctx context.Context, hostname string) ([]string, error) {
	return m.resolveFunc(ctx, hostname)
}

func (m *mockResolver) FallbackToStandard(ctx context.Context, hostname string) ([]string, error) {
	return m.fallbackFunc(ctx, hostname)
}

type mockHandshaker struct {
	handshakeFunc func(ctx context.Context, address string) (any, error)
	fallbackFunc func(ctx context.Context, address string) (any, error)
}

func (m *mockHandshaker) Handshake(ctx context.Context, address string) (any, error) {
	return m.handshakeFunc(ctx, address)
}

func (m *mockHandshaker) FallbackToStandard(ctx context.Context, address string) (any, error) {
	return m.fallbackFunc(ctx, address)
}

type mockDataSender struct {
	sendFunc func(ctx context.Context, data []byte) error
}

func (m *mockDataSender) Send(ctx context.Context, data []byte) error {
	return m.sendFunc(ctx, data)
}

func TestNetworkManager_ResolveDNS(t *testing.T) {
	ctx := context.Background()
	hostname := "example.com"
	expectedIPs := []string{"1.2.3.4"}

	t.Run("DoH Success", func(t *testing.T) {
		mr := &mockResolver{
			resolveFunc: func(ctx context.Context, hostname string) ([]string, error) {
				return expectedIPs, nil
			},
		}
		nm := NewNetworkManagerWithDependencies(nil, mr, nil, nil)
		ips, err := nm.ResolveDNS(ctx, hostname)
		if err != nil || !reflect.DeepEqual(ips, expectedIPs) {
			t.Errorf("ResolveDNS() failed, got %v, want %v, err: %v", ips, expectedIPs, err)
		}
	})

	t.Run("DoH Fail, Fallback Success", func(t *testing.T) {
		mr := &mockResolver{
			resolveFunc: func(ctx context.Context, hostname string) ([]string, error) {
				return nil, errors.New("doh fail")
			},
			fallbackFunc: func(ctx context.Context, hostname string) ([]string, error) {
				return expectedIPs, nil
			},
		}
		nm := NewNetworkManagerWithDependencies(nil, mr, nil, nil)
		ips, err := nm.ResolveDNS(ctx, hostname)
		if err != nil || !reflect.DeepEqual(ips, expectedIPs) {
			t.Errorf("ResolveDNS() fallback failed, got %v, want %v, err: %v", ips, expectedIPs, err)
		}
	})
}

func TestNetworkManager_SecureTLSHandshake(t *testing.T) {
	ctx := context.Background()
	address := "example.com:443"
	expectedState := "tls_state"

	t.Run("Advanced Success", func(t *testing.T) {
		mh := &mockHandshaker{
			handshakeFunc: func(ctx context.Context, address string) (any, error) {
				return expectedState, nil
			},
		}
		nm := NewNetworkManagerWithDependencies(nil, nil, mh, nil)
		state, err := nm.SecureTLSHandshake(ctx, address)
		if err != nil || state != expectedState {
			t.Errorf("SecureTLSHandshake() failed, got %v, want %v, err: %v", state, expectedState, err)
		}
	})
}

func TestNetworkManager_OffloadData(t *testing.T) {
	ctx := context.Background()
	data := []byte("test")

	t.Run("Success", func(t *testing.T) {
		md := &mockDataSender{
			sendFunc: func(ctx context.Context, data []byte) error {
				return nil
			},
		}
		nm := NewNetworkManagerWithDependencies(nil, nil, nil, md)
		err := nm.OffloadData(ctx, data)
		if err != nil {
			t.Errorf("OffloadData() failed, err: %v", err)
		}
	})
}

func TestNetworkManager_UpdateLinkedIP_NoConfig(t *testing.T) {
	nm := NewNetworkManager(nil)
	ctx := context.Background()

	err := nm.UpdateLinkedIP(ctx)
	if err == nil {
		t.Error("UpdateLinkedIP() should error when no endpoints configured, but got nil")
	}
}

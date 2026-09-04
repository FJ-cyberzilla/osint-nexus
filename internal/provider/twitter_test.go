package provider

import (
	"context"
	"net/http"
	"testing"
)

func TestTwitterProvider_CheckUsername(t *testing.T) {
	t.Run("Username found", func(t *testing.T) {
		provider := NewTwitterProvider()
		// Mock the client used by TwitterProvider
		provider.client = &http.Client{
			Transport: RoundTripFunc(func(req *http.Request) *http.Response {
				return &http.Response{
					StatusCode: http.StatusOK,
					Body:       http.NoBody,
				}
			}),
		}

		profile, err := provider.CheckUsername(context.Background(), "testuser")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if profile == nil {
			t.Fatal("expected profile, got nil")
		}
		if profile.Username != "testuser" {
			t.Errorf("expected testuser, got %s", profile.Username)
		}
	})
}

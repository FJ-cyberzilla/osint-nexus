package provider

import (
	"context"
	"net/http"
	"testing"
)

// RoundTripFunc allows us to use a function as a RoundTripper.
type RoundTripFunc func(req *http.Request) *http.Response

func (f RoundTripFunc) RoundTrip(req *http.Request) (*http.Response, error) {
	return f(req), nil
}

func TestGitHubProvider_CheckUsername(t *testing.T) {
	t.Run("Username found", func(t *testing.T) {
		provider := NewGitHubProvider()
		provider.client.Transport = RoundTripFunc(func(req *http.Request) *http.Response {
			return &http.Response{
				StatusCode: http.StatusOK,
				Body:       http.NoBody,
			}
		})

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

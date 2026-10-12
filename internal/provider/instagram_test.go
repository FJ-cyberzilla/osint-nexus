package provider

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestInstagramProvider_CheckUsername(t *testing.T) {
	tests := []struct {
		name           string
		username       string
		serverResponse int
		wantErr        bool
		wantFound      bool
	}{
		{
			name:           "user found",
			username:       "testuser",
			serverResponse: http.StatusOK,
			wantErr:        false,
			wantFound:      true,
		},
		{
			name:           "user not found",
			username:       "nonexistent",
			serverResponse: http.StatusNotFound,
			wantErr:        false,
			wantFound:      false,
		},
		{
			name:           "server error",
			username:       "testuser",
			serverResponse: http.StatusInternalServerError,
			wantErr:        true,
			wantFound:      false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(tt.serverResponse)
			}))
			defer server.Close()

			p := NewInstagramProviderWithURL(server.URL)
			profile, err := p.CheckUsername(context.Background(), tt.username)

			if tt.wantErr {
				if err == nil {
					t.Errorf("expected error, got nil")
				}
				return
			}

			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if tt.wantFound {
				if profile == nil {
					t.Fatalf("expected profile, got nil")
				}
				if profile.Username != tt.username {
					t.Errorf("expected username %s, got %s", tt.username, profile.Username)
				}
			} else {
				if profile != nil {
					t.Errorf("expected nil profile, got %+v", profile)
				}
			}
		})
	}
}

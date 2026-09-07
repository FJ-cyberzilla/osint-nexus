package provider

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
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
				assert.Error(t, err)
				return
			}

			require.NoError(t, err)
			if tt.wantFound {
				assert.NotNil(t, profile)
				assert.Equal(t, tt.username, profile.Username)
			} else {
				assert.Nil(t, profile)
			}
		})
	}
}

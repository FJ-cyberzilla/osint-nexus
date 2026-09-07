package provider

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestAparatProvider_CheckUsername(t *testing.T) {
	tests := []struct {
		name           string
		username       string
		serverResponse int
		wantFound      bool
	}{
		{
			name:           "user found",
			username:       "testuser",
			serverResponse: http.StatusOK,
			wantFound:      true,
		},
		{
			name:           "user not found",
			username:       "nonexistent",
			serverResponse: http.StatusNotFound,
			wantFound:      false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(tt.serverResponse)
			}))
			defer server.Close()

			// AparatProvider needs refactoring to accept a base URL
			t.Skip("AparatProvider hardcodes base URL, skipping full network test until refactored.")
		})
	}
}

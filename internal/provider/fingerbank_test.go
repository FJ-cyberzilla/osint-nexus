package provider

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestFingerbankClient_Interrogate(t *testing.T) {
	expectedResponse := types.FingerbankInterrogateResponse{
		Device: types.Device{
			ID:              "123",
			Name:            "TestDevice",
			Vendor:          "TestVendor",
			DeviceType:      "Laptop",
			OperatingSystem: "Linux",
		},
		DeviceName:      "TestDevice",
		Score:           99,
		Version:         "1.0",
		RequestId:       "req123",
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, http.MethodPost, r.Method)
		assert.Contains(t, r.URL.Path, "/combinations/interrogate")
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(expectedResponse)
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	payload := types.FingerbankPayload{
		Hostname: "test.com",
	}
	result, err := client.Interrogate(context.Background(), payload)

	require.NoError(t, err)
	assert.Equal(t, &expectedResponse, result)
}

func TestFingerbankClient_GetDevice(t *testing.T) {
	expectedDevice := types.Device{
		ID:              "123",
		Name:            "TestDevice",
		Vendor:          "TestVendor",
		DeviceType:      "Laptop",
		OperatingSystem: "Linux",
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, http.MethodGet, r.Method)
		assert.Contains(t, r.URL.Path, "/devices/123")
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(expectedDevice)
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	result, err := client.GetDevice(context.Background(), "123")

	require.NoError(t, err)
	assert.Equal(t, &expectedDevice, result)
}

func TestFingerbankClient_GetDeviceProfilingRules(t *testing.T) {
	expectedRules := []types.ProfilingRule{
		{ID: "rule1", Rule: "rule_data_1"},
		{ID: "rule2", Rule: "rule_data_2"},
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, http.MethodGet, r.Method)
		assert.Contains(t, r.URL.Path, "/devices/123/profiling_rules")
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(expectedRules)
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	result, err := client.GetDeviceProfilingRules(context.Background(), "123")

	require.NoError(t, err)
	assert.Equal(t, expectedRules, result)
}

func TestFingerbankClient_GetDeviceVulnerabilities(t *testing.T) {
	expectedVulnerabilities := []types.Vulnerability{
		{ID: "vuln1", Description: "desc1"},
		{ID: "vuln2", Description: "desc2"},
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, http.MethodGet, r.Method)
		assert.Contains(t, r.URL.Path, "/devices/123/vulnerabilities")
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(expectedVulnerabilities)
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	result, err := client.GetDeviceVulnerabilities(context.Background(), "123")

	require.NoError(t, err)
	assert.Equal(t, expectedVulnerabilities, result)
}

func TestFingerbankClient_IsDeviceA(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, http.MethodGet, r.Method)
		assert.Contains(t, r.URL.Path, "/devices/123/is_a/456")
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(types.IsAResponse{IsA: true})
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	result, err := client.IsDeviceA(context.Background(), "123", "456")

	require.NoError(t, err)
	assert.True(t, result)
}



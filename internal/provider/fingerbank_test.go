package provider

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
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
		DeviceName: "TestDevice",
		Score:      99,
		Version:    "1.0",
		RequestId:  "req123",
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if !strings.Contains(r.URL.Path, "/combinations/interrogate") {
			t.Errorf("expected path to contain /combinations/interrogate, got %s", r.URL.Path)
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(expectedResponse)
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	payload := types.FingerbankPayload{
		Hostname: "test.com",
	}
	result, err := client.Interrogate(context.Background(), payload)

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !reflect.DeepEqual(&expectedResponse, result) {
		t.Errorf("got %+v, want %+v", result, &expectedResponse)
	}
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
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if !strings.Contains(r.URL.Path, "/devices/123") {
			t.Errorf("expected path to contain /devices/123, got %s", r.URL.Path)
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(expectedDevice)
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	result, err := client.GetDevice(context.Background(), "123")

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !reflect.DeepEqual(&expectedDevice, result) {
		t.Errorf("got %+v, want %+v", result, &expectedDevice)
	}
}

func TestFingerbankClient_GetDeviceProfilingRules(t *testing.T) {
	expectedRules := []types.ProfilingRule{
		{ID: "rule1", Rule: "rule_data_1"},
		{ID: "rule2", Rule: "rule_data_2"},
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if !strings.Contains(r.URL.Path, "/devices/123/profiling_rules") {
			t.Errorf("expected path to contain /devices/123/profiling_rules, got %s", r.URL.Path)
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(expectedRules)
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	result, err := client.GetDeviceProfilingRules(context.Background(), "123")

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !reflect.DeepEqual(expectedRules, result) {
		t.Errorf("got %+v, want %+v", result, expectedRules)
	}
}

func TestFingerbankClient_GetDeviceVulnerabilities(t *testing.T) {
	expectedVulnerabilities := []types.Vulnerability{
		{ID: "vuln1", Description: "desc1"},
		{ID: "vuln2", Description: "desc2"},
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if !strings.Contains(r.URL.Path, "/devices/123/vulnerabilities") {
			t.Errorf("expected path to contain /devices/123/vulnerabilities, got %s", r.URL.Path)
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(expectedVulnerabilities)
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	result, err := client.GetDeviceVulnerabilities(context.Background(), "123")

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !reflect.DeepEqual(expectedVulnerabilities, result) {
		t.Errorf("got %+v, want %+v", result, expectedVulnerabilities)
	}
}

func TestFingerbankClient_IsDeviceA(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if !strings.Contains(r.URL.Path, "/devices/123/is_a/456") {
			t.Errorf("expected path to contain /devices/123/is_a/456, got %s", r.URL.Path)
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(types.IsAResponse{IsA: true})
	}))
	defer server.Close()

	client := NewFingerbankClientWithURL("test-api-key", server.URL)
	result, err := client.IsDeviceA(context.Background(), "123", "456")

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !result {
		t.Errorf("expected true, got false")
	}
}

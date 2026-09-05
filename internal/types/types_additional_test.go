package types

import (
	"testing"
	"time"
)

type TestPayload struct{ Key string }

func (p TestPayload) PayloadType() string { return "test" }

func TestErrors(t *testing.T) {
	if ErrNexus.Error() != "nexus error" {
		t.Error("ErrNexus content mismatch")
	}
	if ErrConfiguration.Error() != "configuration error" {
		t.Error("ErrConfiguration content mismatch")
	}
}

func TestFingerprintStructs(t *testing.T) {
	fd := FingerprintData{
		Type:    "tls",
		Payload: TestPayload{Key: "value"},
	}
	if fd.Type != "tls" {
		t.Error("FingerprintData instantiation failed")
	}

	fr := FingerprintResult{
		Name:       "test",
		Data:       fd,
		Confidence: 1.0,
	}
	if fr.Name != "test" {
		t.Error("FingerprintResult instantiation failed")
	}
}

func TestScanResult(t *testing.T) {
	sr := ScanResult{
		ID:        1,
		Username:  "user",
		Platform:  "twitter",
		Found:     true,
		Timestamp: time.Now(),
	}
	if sr.Username != "user" {
		t.Error("ScanResult instantiation failed")
	}
}

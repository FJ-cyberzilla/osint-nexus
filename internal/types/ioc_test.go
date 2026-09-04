package types

import (
	"testing"
)

func TestIOCStructs(t *testing.T) {
	// Simple test to ensure types are instantiable and usable
	ioc := ExtractedIOC{
		Type:  IOCTypeIPv4,
		Value: "127.0.0.1",
	}
	if ioc.Value != "127.0.0.1" {
		t.Error("ioc struct instantiation failed")
	}

	pivot := ExtractedPivots{
		Emails: []string{"test@example.com"},
	}
	if len(pivot.Emails) != 1 {
		t.Error("pivot struct instantiation failed")
	}
}

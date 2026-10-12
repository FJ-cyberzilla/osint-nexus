package network

import (
	"strings"
	"testing"
)

func TestNewNextDNSEndpoints(t *testing.T) {
	id := "b13e8b"
	key := "8e55389efbdbcc98"
	ep := NewNextDNSEndpoints(id, key)

	if ep.ID != id {
		t.Errorf("expected ID %s, got %s", id, ep.ID)
	}
	if ep.Key != key {
		t.Errorf("expected Key %s, got %s", key, ep.Key)
	}
	if ep.DoT != "b13e8b.dns.nextdns.io" {
		t.Errorf("expected DoT b13e8b.dns.nextdns.io, got %s", ep.DoT)
	}
	if ep.DoH != "https://dns.nextdns.io/b13e8b" {
		t.Errorf("expected DoH https://dns.nextdns.io/b13e8b, got %s", ep.DoH)
	}
	if ep.LinkIPURL != "https://link-ip.nextdns.io/b13e8b/8e55389efbdbcc98" {
		t.Errorf("expected LinkIPURL, got %s", ep.LinkIPURL)
	}
	foundIPv61 := false
	foundIPv62 := false
	for _, ip := range ep.IPv6 {
		if strings.Contains(ip, "2a07:a8c0::b13e8b") {
			foundIPv61 = true
		}
		if strings.Contains(ip, "2a07:a8c1::b13e8b") {
			foundIPv62 = true
		}
	}
	if !foundIPv61 || !foundIPv62 {
		t.Errorf("expected IPv6 addresses containing 2a07:a8c0::b13e8b and 2a07:a8c1::b13e8b, got %v", ep.IPv6)
	}
}

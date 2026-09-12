package network

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewNextDNSEndpoints(t *testing.T) {
	id := "b13e8b"
	key := "8e55389efbdbcc98"
	ep := NewNextDNSEndpoints(id, key)

	assert.Equal(t, id, ep.ID)
	assert.Equal(t, key, ep.Key)
	assert.Equal(t, "b13e8b.dns.nextdns.io", ep.DoT)
	assert.Equal(t, "https://dns.nextdns.io/b13e8b", ep.DoH)
	assert.Equal(t, "https://link-ip.nextdns.io/b13e8b/8e55389efbdbcc98", ep.LinkIPURL)
	assert.Contains(t, ep.IPv6, "2a07:a8c0::b13e8b")
	assert.Contains(t, ep.IPv6, "2a07:a8c1::b13e8b")
}

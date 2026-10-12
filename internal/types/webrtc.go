package types

import (
	"net"
)

// WebRTCCandidateType defines the category of an ICE candidate.
type WebRTCCandidateType string

const (
	// Host: Local network interface endpoint. Reveals internal LAN IPs (RFC 1918) and interface types.
	CandidateHost WebRTCCandidateType = "host"
	// Srflx: Server Reflexive (via STUN). Discovers the client's public NAT IP address and external port.
	CandidateSrflx WebRTCCandidateType = "srflx"
	// Prflx: Peer Reflexive. Discovered directly by the peer during connectivity checks.
	CandidatePrflx WebRTCCandidateType = "prflx"
	// Relay: Relayed candidate (via TURN). Shows TURN proxy relay addresses (hides client direct IP).
	CandidateRelay WebRTCCandidateType = "relay"
)

// IceCandidate represents the extracted metadata from an ICE candidate string.
type IceCandidate struct {
	Foundation string              `json:"foundation"`
	Component  int                 `json:"component"`
	Protocol   string              `json:"protocol"`
	Priority   uint32              `json:"priority"`
	Address    net.IP              `json:"address"`
	Port       int                 `json:"port"`
	Type       WebRTCCandidateType `json:"type"`
	RelAddr    net.IP              `json:"rel_addr,omitempty"`
	RelPort    int                 `json:"rel_port,omitempty"`
}

// String returns the string representation of the candidate type.
func (t WebRTCCandidateType) String() string {
	return string(t)
}

// IsPublic returns true if the candidate's IP address is a globally routable public IP.
func (c *IceCandidate) IsPublic() bool {
	if c.Address == nil {
		return false
	}

	// Filter out non-routable, loopback, multicast, and private ranges
	if c.Address.IsLoopback() ||
		c.Address.IsLinkLocalUnicast() ||
		c.Address.IsLinkLocalMulticast() ||
		c.Address.IsUnspecified() ||
		c.Address.IsPrivate() {
		return false
	}

	// Extra check for CGNAT range (100.64.0.0/10) if needed
	if isCGNAT(c.Address) {
		return false
	}

	return true
}

// CGNAT block (100.64.0.0/10) - RFC 6598
var cgnatNet = &net.IPNet{
	IP:   net.ParseIP("100.64.0.0"),
	Mask: net.CIDRMask(10, 32),
}

func isCGNAT(ip net.IP) bool {
	return cgnatNet.Contains(ip)
}

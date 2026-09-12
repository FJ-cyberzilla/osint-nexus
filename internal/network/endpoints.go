package network

// Endpoints holds network configuration for DNS/TLS services.
type Endpoints struct {
	ID        string
	Key       string
	DoT       string
	DoH       string
	IPv6      []string
	LinkIPURL string
}

// NewNextDNSEndpoints creates a preconfigured Endpoints struct for NextDNS.
func NewNextDNSEndpoints(id, key string) *Endpoints {
	return &Endpoints{
		ID:  id,
		Key: key,
		DoT: id + ".dns.nextdns.io",
		DoH: "https://dns.nextdns.io/" + id,
		IPv6: []string{
			"2a07:a8c0::" + id,
			"2a07:a8c1::" + id,
		},
		LinkIPURL: "https://link-ip.nextdns.io/" + id + "/" + key,
	}
}

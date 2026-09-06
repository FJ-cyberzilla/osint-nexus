package types

import "fmt"

// FingerbankPayload models the request payload for Fingerbank API v2.
type FingerbankPayload struct {
	ClientHints            map[string]map[string]string `json:"client_hints,omitempty"`
	DHCPFingerprint        string                       `json:"dhcp_fingerprint,omitempty"`
	DHCP6Fingerprint       string                       `json:"dhcp6_fingerprint,omitempty"`
	DHCPVendor             string                       `json:"dhcp_vendor,omitempty"`
	DHCP6Enterprise        string                       `json:"dhcp6_enterprise,omitempty"`
	MAC                    string                       `json:"mac,omitempty"`
	DestinationHosts       []string                     `json:"destination_hosts,omitempty"`
	Hostname               string                       `json:"hostname,omitempty"`
	JA3Fingerprints        []string                     `json:"ja3_fingerprints,omitempty"`
	JA3Data                map[string][]string          `json:"ja3_data,omitempty"`
	MDNSServices           []string                     `json:"mdns_services,omitempty"`
	UPnPUserAgents         []string                     `json:"upnp_user_agents,omitempty"`
	UPnPServerStrings      []string                     `json:"upnp_server_strings,omitempty"`
	TCPSynSignatures       []string                     `json:"tcp_syn_signatures,omitempty"`
	TCPSynAckSignatures    []string                     `json:"tcp_syn_ack_signatures,omitempty"`
	UserAgents             []string                     `json:"user_agents,omitempty"`
}

// FingerbankInterrogateResponse models the response from Fingerbank API v2.
type FingerbankInterrogateResponse struct {
	Device          Device           `json:"device"`
	DeviceName      string           `json:"device_name"`
	Manufacturer    Device           `json:"manufacturer"`
	OperatingSystem Device           `json:"operating_system"`
	Score           int              `json:"score"`
	Version         string           `json:"version"`
	Vulnerabilities Vulnerabilities  `json:"vulnerabilities"`
	RequestId       string           `json:"request_id"`
}

// Vulnerabilities models CVE vulnerabilities.
type Vulnerabilities struct {
	CveDevices map[string]interface{} `json:"cve_devices"`
	CveOs      map[string]interface{} `json:"cve_os"`
	Message    string                 `json:"message"`
}

// Device models a device response.
type Device struct {
	ID              string `json:"id"`
	Name            string `json:"name"`
	Vendor          string `json:"vendor"`
	DeviceType      string `json:"device_type"`
	OperatingSystem string `json:"operating_system"`
}

// DeviceBaseInfo models base device info.
type DeviceBaseInfo struct {
	TotalDevices int `json:"total_devices"`
}

// Vulnerability models a vulnerability response.
type Vulnerability struct {
	ID          string `json:"id"`
	Description string `json:"description"`
}

// ProfilingRule models a profiling rule response.
type ProfilingRule struct {
	ID   string `json:"id"`
	Rule string `json:"rule"`
}

// IsAResponse models the response for is_a check.
type IsAResponse struct {
	IsA bool `json:"is_a"`
}

// FingerbankError defines custom errors for Fingerbank provider.
type FingerbankError struct {
	Message string
	Code    int
}

func (e *FingerbankError) Error() string {
	return fmt.Sprintf("fingerbank error: %s (code: %d)", e.Message, e.Code)
}

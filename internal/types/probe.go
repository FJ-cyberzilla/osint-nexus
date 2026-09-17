package types

// ProbeResult holds the outcome of a protocol probe.
type ProbeResult struct {
	Target    string            `json:"target" yaml:"target"`
	Protocol  string            `json:"protocol" yaml:"protocol"`
	Supported bool              `json:"supported" yaml:"supported"`
	Metadata  map[string]string `json:"metadata" yaml:"metadata"`
}

package strategies

import (
	"context"
	"strings"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// HTTPPayload implements types.FingerprintPayload for HTTP fingerprinting input.
type HTTPPayload struct {
	Headers map[string]string `json:"headers"`
}

// PayloadType returns the payload type identifier.
func (p HTTPPayload) PayloadType() string { return "http_input" }

// HTTPOutputPayload implements types.FingerprintPayload for HTTP fingerprinting output.
type HTTPOutputPayload struct {
	Platform     string            `json:"platform"`
	Mobile       bool              `json:"mobile"`
	Architecture string            `json:"architecture"`
	Language     string            `json:"language"`
	FullHeaders  map[string]string `json:"full_headers"`
}

// PayloadType returns the payload type identifier.
func (p HTTPOutputPayload) PayloadType() string { return "http_output" }

// HttpFingerprintStrategy identifies device info based on HTTP headers.
type HttpFingerprintStrategy struct{}

// NewHttpFingerprintStrategy initializes a new HttpFingerprintStrategy.
func NewHttpFingerprintStrategy() *HttpFingerprintStrategy {
	return &HttpFingerprintStrategy{}
}

// Name returns the strategy identifier.
func (s *HttpFingerprintStrategy) Name() string {
	return "http_headers"
}

// Extract analyzes HTTP headers to extract device information.
func (s *HttpFingerprintStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	payload, ok := data.Payload.(HTTPPayload)
	if !ok {
		return types.FingerprintResult{
			Name: s.Name(),
			Data: types.FingerprintData{
				Type:    "http_headers",
				Payload: HTTPOutputPayload{},
			},
			Confidence: 0.85,
		}, nil
	}

	headers := make(map[string]string)
	for k, v := range payload.Headers {
		headers[strings.ToLower(k)] = v
	}

	secChUaHeaders := make(map[string]string)
	for k, v := range payload.Headers {
		if strings.HasPrefix(strings.ToLower(k), "sec-ch-ua") {
			secChUaHeaders[k] = v
		}
	}

	return types.FingerprintResult{
		Name: s.Name(),
		Data: types.FingerprintData{
			Type: "http_headers",
			Payload: HTTPOutputPayload{
				Platform:     headers["sec-ch-ua-platform"],
				Mobile:       headers["sec-ch-ua-mobile"] == "?1",
				Architecture: headers["sec-ch-ua-arch"],
				Language:     headers["accept-language"],
				FullHeaders:  secChUaHeaders,
			},
		},
		Confidence: 0.85,
	}, nil
}

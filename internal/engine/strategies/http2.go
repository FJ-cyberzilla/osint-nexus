package strategies

import (
	"context"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// HTTP2Settings defines the structured configuration for HTTP/2.
type HTTP2Settings struct {
	HeaderTableSize      *int  `json:"header_table_size"`
	EnablePush           *bool `json:"enable_push"`
	MaxConcurrentStreams *int  `json:"max_concurrent_streams"`
	InitialWindowSize    *int  `json:"initial_window_size"`
	MaxFrameSize         *int  `json:"max_frame_size"`
	MaxHeaderListSize    *int  `json:"max_header_list_size"`
}

// HTTP2Payload implements types.FingerprintPayload for HTTP2/3 fingerprinting input.
type HTTP2Payload struct {
	ALPN          string        `json:"alpn"`
	SettingsFrame HTTP2Settings `json:"settings_frame"`
}

// PayloadType returns the payload type identifier.
func (p HTTP2Payload) PayloadType() string { return "http2_3_input" }

// HTTP2OutputPayload implements types.FingerprintPayload for HTTP2/3 fingerprinting output.
type HTTP2OutputPayload struct {
	Protocol             string `json:"protocol"`
	SettingsCount        int    `json:"settings_count"`
	MaxConcurrentStreams int    `json:"max_concurrent_streams"`
}

// PayloadType returns the payload type identifier.
func (p HTTP2OutputPayload) PayloadType() string { return "http2_3_output" }

// Http2FingerprintStrategy identifies HTTP/2 & 3 stack info.
type Http2FingerprintStrategy struct{}

// NewHttp2FingerprintStrategy initializes a new Http2FingerprintStrategy.
func NewHttp2FingerprintStrategy() *Http2FingerprintStrategy {
	return &Http2FingerprintStrategy{}
}

// Name returns the strategy identifier.
func (s *Http2FingerprintStrategy) Name() string {
	return "http2_3_stack"
}

// Extract analyzes ALPN and settings to detect HTTP/2/3.
func (s *Http2FingerprintStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	payload, ok := data.Payload.(HTTP2Payload)
	if !ok {
		return types.FingerprintResult{}, nil
	}

	maxConcurrentStreams := 100
	if payload.SettingsFrame.MaxConcurrentStreams != nil {
		maxConcurrentStreams = *payload.SettingsFrame.MaxConcurrentStreams
	}

	confidence := 0.2
	if payload.ALPN == "h2" || payload.ALPN == "h3" {
		confidence = 0.7
	}

	return types.FingerprintResult{
		Name: s.Name(),
		Data: types.FingerprintData{
			Type: "http2_3_detection",
			Payload: HTTP2OutputPayload{
				Protocol:             payload.ALPN,
				SettingsCount:        6, // Constant value for defined struct fields
				MaxConcurrentStreams: maxConcurrentStreams,
			},
		},
		Confidence: confidence,
	}, nil
}

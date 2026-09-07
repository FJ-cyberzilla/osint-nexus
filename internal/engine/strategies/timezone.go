package strategies

import (
	"context"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// TimezonePayload implements types.FingerprintPayload for Timezone fingerprinting input.
type TimezonePayload struct {
	Timezone      string `json:"timezone"`
	OffsetSeconds int    `json:"offset_seconds"`
}

// PayloadType returns the payload type identifier.
func (p TimezonePayload) PayloadType() string { return "timezone_input" }

// TimezoneOutputPayload implements types.FingerprintPayload for Timezone fingerprinting output.
type TimezoneOutputPayload struct {
	Timezone      string `json:"timezone"`
	OffsetSeconds int    `json:"offset_seconds"`
}

// PayloadType returns the payload type identifier.
func (p TimezoneOutputPayload) PayloadType() string { return "timezone_output" }

// TimezoneFingerprintStrategy identifies timezone/NTP information.
type TimezoneFingerprintStrategy struct{}

// NewTimezoneFingerprintStrategy initializes a new TimezoneFingerprintStrategy.
func NewTimezoneFingerprintStrategy() *TimezoneFingerprintStrategy {
	return &TimezoneFingerprintStrategy{}
}

// Name returns the strategy identifier.
func (s *TimezoneFingerprintStrategy) Name() string {
	return "timezone_ntp"
}

// Extract analyzes timezone and offset information.
func (s *TimezoneFingerprintStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	payload, ok := data.Payload.(TimezonePayload)
	if !ok {
		return types.FingerprintResult{
			Name: s.Name(),
			Data: types.FingerprintData{
				Type:    "timezone_detection",
				Payload: TimezoneOutputPayload{},
			},
			Confidence: 0.0,
		}, nil
	}

	confidence := 0.5
	if payload.Timezone == "" {
		confidence = 0.1
	}

	return types.FingerprintResult{
		Name: s.Name(),
		Data: types.FingerprintData{
			Type:    "timezone_detection",
			Payload: TimezoneOutputPayload{Timezone: payload.Timezone, OffsetSeconds: payload.OffsetSeconds},
		},
		Confidence: confidence,
	}, nil
}

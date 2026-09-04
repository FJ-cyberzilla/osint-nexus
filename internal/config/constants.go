package config

// Project-wide constants for OSINT Nexus.

const (
	Version       = "4.1.1"
	ColorOrange   = "bold orange1"
	ColorTip      = "yellow"
	JitterMin     = 1.0
	JitterMax     = 3.0
	DefaultTimeout = 10
	RetryAttempts  = 3
	BackoffFactor  = 0.5
)

// DeviceInference holds constants for device inference.
const (
	DeviceUnidentified   = "Unidentified"
	DeviceUnknown        = "Unknown"
	MinConfidence        = 0.0
	MaxConfidence        = 1.0
	RegexMatchConfidence = 0.8
)

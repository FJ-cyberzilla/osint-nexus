package types

import "errors"

// NexusError base errors for all OSINT Nexus framework errors.
var (
	ErrNexus         = errors.New("nexus error")
	ErrConfiguration = errors.New("configuration error")
	ErrProvider      = errors.New("provider error")
	ErrNetwork       = errors.New("network error")
	ErrValidation    = errors.New("validation error")
	ErrDatabase      = errors.New("database error")
)

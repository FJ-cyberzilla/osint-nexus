package types

import "strings"

// UnknownKind classifies why a value is unknown.
type UnknownKind uint8

const (
	KindNone UnknownKind = iota
	KindNotCollected
	KindNotAvailable
	KindNotApplicable
	KindRedacted
	KindConflicting
	KindStale
	KindSourceError
)

var unknownKindNames = [...]string{
	"none",
	"not_collected",
	"not_available",
	"not_applicable",
	"redacted",
	"conflicting",
	"stale",
	"source_error",
}

func (k UnknownKind) String() string {
	if int(k) < len(unknownKindNames) {
		return unknownKindNames[k]
	}
	return "invalid"
}

func (k UnknownKind) MarshalText() ([]byte, error) {
	return []byte(k.String()), nil
}

func (k *UnknownKind) UnmarshalText(b []byte) error {
	s := strings.TrimSpace(strings.ToLower(string(b)))
	for i, name := range unknownKindNames {
		if name == s {
			*k = UnknownKind(i)
			return nil
		}
	}
	return &UnknownKindError{Raw: s}
}

type UnknownKindError struct{ Raw string }

func (e *UnknownKindError) Error() string { return "types: unknown kind " + e.Raw }

// Display constants — presentation only. Do not compare against these.
const (
	Unknown      = "Unknown"
	UnknownLower = "unknown"
)

var unknownAliases = map[string]struct{}{
	"": {}, "-": {}, "n/a": {}, "na": {}, "n.a.": {},
	"null": {}, "nil": {}, "none": {}, "undefined": {},
	"not found": {}, "not_found": {}, "unknown": {},
}

// IsUnknown reports whether s is a recognized null/unknown sentinel.
func IsUnknown(s string) bool {
	_, ok := unknownAliases[strings.ToLower(strings.TrimSpace(s))]
	return ok
}

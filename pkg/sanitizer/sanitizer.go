package sanitizer

import (
	"regexp"
	"strings"
)

var (
	// sanitizedUsernameRegex ensures usernames contain only alphanumeric characters and underscores.
	sanitizedUsernameRegex = regexp.MustCompile(`^[a-zA-Z0-9_]+$`)
)

// SanitizeUsername cleans a username input, returning a sanitized string and a boolean indicating validity.
func SanitizeUsername(username string) (string, bool) {
	sanitized := strings.TrimSpace(username)
	if sanitized == "" {
		return "", false
	}

	if !sanitizedUsernameRegex.MatchString(sanitized) {
		return "", false
	}

	return sanitized, true
}

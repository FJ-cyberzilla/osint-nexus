package detector

import (
	"net"
	"strconv"
	"strings"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// ParseIceCandidate parses an ICE candidate string (RFC 8445 / RFC 8838) into a
// structured IceCandidate. It accepts both raw ("candidate:...") and SDP-framed
// ("a=candidate:...") forms. All numeric fields are range-checked, IPs are
// validated, and optional attributes (raddr, rport, tcptype) are preserved.
//
// The returned error always identifies the offending token and its position so
// that malformed input can be traced without re-instrumenting callers.
func ParseIceCandidate(raw string) (*types.IceCandidate, error) {
	if raw == "" {
		return nil, eris.New("detector: empty ICE candidate")
	}

	// Normalize SDP framing and the "candidate:" prefix. TrimPrefix is called
	// once per prefix; order matters because SDP wraps the candidate prefix.
	raw = strings.TrimSpace(raw)
	raw = strings.TrimPrefix(raw, "a=")
	raw = strings.TrimPrefix(raw, "candidate:")

	tokens := strings.Fields(raw)

	// Minimum grammar:
	//   foundation component transport priority address port "typ" type
	// = 8 tokens. Extension attributes (raddr/rport/tcptype/...) follow in
	// key/value pairs but may also appear as standalone keys (e.g. "generation"),
	// so we validate the fixed prefix first, then walk the tail.
	if len(tokens) < 8 {
		return nil, eris.Errorf(
			"detector: ICE candidate has %d tokens, need at least 8", len(tokens))
	}

	// ---- Fixed prefix -------------------------------------------------------

	foundation := tokens[0]
	if foundation == "" || len(foundation) > 32 {
		return nil, eris.Errorf(
			"detector: invalid foundation %q (length must be 1..32)", foundation)
	}

	component, err := parseIntRange(tokens[1], 1, 256)
	if err != nil {
		return nil, eris.Wrapf(err, "detector: component %q", tokens[1])
	}

	transport, err := parseTransport(tokens[2])
	if err != nil {
		return nil, eris.Wrapf(err, "detector: transport %q", tokens[2])
	}

	priority, err := strconv.ParseUint(tokens[3], 10, 32)
	if err != nil {
		return nil, eris.Wrapf(err, "detector: priority %q", tokens[3])
	}

	// RFC 8838 allows mDNS hostnames (e.g. "abcd-1234.local") in place of an
	// IP for host candidates. We try IP first and fall back to a hostname.
	addr, hostname, err := parseAddress(tokens[4])
	if err != nil {
		return nil, eris.Wrapf(err, "detector: address %q", tokens[4])
	}

	port, err := parseIntRange(tokens[5], 1, 65535)
	if err != nil {
		return nil, eris.Wrapf(err, "detector: port %q", tokens[5])
	}

	if tokens[6] != "typ" {
		return nil, eris.Errorf(
			"detector: expected \"typ\" at index 6, got %q", tokens[6])
	}

	candType, err := parseCandidateType(tokens[7])
	if err != nil {
		return nil, eris.Wrapf(err, "detector: candidate type %q", tokens[7])
	}

	candidate := &types.IceCandidate{
		Foundation: foundation,
		Component:  component,
		Protocol:   transport,
		Priority:   uint32(priority),
		Address:    addr,
		Hostname:   hostname, // "" when Address is a literal IP
		Port:       port,
		Type:       candType,
	}

	// ---- Extension attributes ----------------------------------------------

	// Walk the tail as key/value pairs. RFC 8445 extension-att is
	// "SP extension-att-name SP extension-att-value", so malformed tails
	// (odd token count) are rejected rather than silently truncated.
	tail := tokens[8:]
	if len(tail)%2 != 0 {
		return nil, eris.Errorf(
			"detector: dangling attribute key %q without value", tail[len(tail)-1])
	}

	for i := 0; i < len(tail); i += 2 {
		key, val := tail[i], tail[i+1]
		switch key {
		case "raddr":
			relIP := net.ParseIP(val)
			if relIP == nil {
				return nil, eris.Errorf(
					"detector: invalid raddr IP %q", val)
			}
			candidate.RelAddr = relIP

		case "rport":
			relPort, err := parseUintRange(val, 1, 65535)
			if err != nil {
				return nil, eris.Wrapf(err, "detector: rport %q", val)
			}
			candidate.RelPort = int(relPort)

		case "tcptype":
			// RFC 6544: active | passive | so
			switch val {
			case "active", "passive", "so":
				candidate.TCPType = val
			default:
				return nil, eris.Errorf(
					"detector: invalid tcptype %q", val)
			}

		default:
			// Unknown but well-formed attribute: preserve for forward
			// compatibility instead of silently dropping it.
			if candidate.Attributes == nil {
				candidate.Attributes = make(map[string]string, 2)
			}
			candidate.Attributes[key] = val
		}
	}

	return candidate, nil
}

// ParseIceCandidates parses a slice of ICE candidate strings into structured candidates and errors.
func ParseIceCandidates(rawLines []string) ([]*types.IceCandidate, []error) {
	var candidates []*types.IceCandidate
	var errs []error
	for _, line := range rawLines {
		c, err := ParseIceCandidate(line)
		if err != nil {
			errs = append(errs, err)
			continue
		}
		if c != nil {
			candidates = append(candidates, c)
		}
	}
	return candidates, errs
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

// parseIntRange parses a base-10 signed integer and enforces [min, max].
func parseIntRange(s string, min, max int) (int, error) {
	if s == "" {
		return 0, eris.New("empty numeric value")
	}
	v, err := strconv.ParseInt(s, 10, strconv.IntSize)
	if err != nil {
		return 0, eris.Wrapf(err, "not a valid integer")
	}
	iv := int(v)
	if iv < min || iv > max {
		return 0, eris.Errorf("value %d out of range [%d, %d]", iv, min, max)
	}
	return iv, nil
}

// parseUintRange parses a base-10 unsigned integer and enforces [min, max].
// It rejects signs, whitespace, and overflow beyond max.
func parseUintRange(s string, min, max uint64) (uint64, error) {
	if s == "" {
		return 0, eris.New("empty numeric value")
	}
	// ParseUint rejects '+'/'-' and non-digits; bitSize 64 with explicit max
	// check avoids platform-dependent truncation.
	v, err := strconv.ParseUint(s, 10, 64)
	if err != nil {
		return 0, eris.Wrapf(err, "not a valid unsigned integer")
	}
	if v < min || v > max {
		return 0, eris.Errorf("value %d out of range [%d, %d]", v, min, max)
	}
	return v, nil
}

// parseTransport normalizes and validates the transport token.
// RFC 8445 defines "UDP" and "TCP" (case-insensitive on the wire).
func parseTransport(s string) (string, error) {
	switch strings.ToUpper(s) {
	case "UDP":
		return "udp", nil
	case "TCP":
		return "tcp", nil
	default:
		return "", eris.Errorf("unsupported transport (want UDP or TCP)")
	}
}

// parseCandidateType maps the wire token to the project's enum.
// Adjust the switch to match types.WebRTCCandidateType's actual values.
func parseCandidateType(s string) (types.WebRTCCandidateType, error) {
	switch s {
	case "host", "srflx", "prflx", "relay":
		return types.WebRTCCandidateType(s), nil
	default:
		return "", eris.Errorf("unknown candidate type")
	}
}

// parseAddress accepts either a literal IP or an mDNS/hostname token.
// Exactly one of (ip, hostname) is non-nil/non-empty on success.
func parseAddress(s string) (net.IP, string, error) {
	if ip := net.ParseIP(s); ip != nil {
		return ip, "", nil
	}
	// RFC 8838 mDNS names end in ".local"; some stacks emit bare hostnames.
	// We accept any syntactically valid DNS label sequence rather than
	// rejecting modern browser candidates.
	if isHostname(s) {
		return nil, s, nil
	}
	return nil, "", eris.New("not a valid IP or hostname")
}

// isHostname performs a light syntactic check: non-empty, <=253 chars,
// labels separated by '.', each label 1..63 chars of [A-Za-z0-9-],
// no leading/trailing hyphen. It does not do DNS resolution.
func isHostname(s string) bool {
	if s == "" || len(s) > 253 {
		return false
	}
	// Trailing dot is legal in FQDN form; strip it for label checking.
	s = strings.TrimSuffix(s, ".")
	if s == "" {
		return false
	}
	for _, label := range strings.Split(s, ".") {
		if len(label) == 0 || len(label) > 63 {
			return false
		}
		if label[0] == '-' || label[len(label)-1] == '-' {
			return false
		}
		for i := 0; i < len(label); i++ {
			c := label[i]
			switch {
			case c >= 'a' && c <= 'z',
				c >= 'A' && c <= 'Z',
				c >= '0' && c <= '9',
				c == '-':
				// ok
			default:
				return false
			}
		}
	}
	return true
}

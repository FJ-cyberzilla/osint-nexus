package strategies

import (
	"context"
	"net"
	"syscall"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// TCPSocketConfig holds tuning parameters for raw TCP sockets (TTL, Window Size, KeepAlive).
type TCPSocketConfig struct {
	TTL        int           `json:"ttl" yaml:"ttl"`
	WindowSize int           `json:"window_size" yaml:"window_size"`
	KeepAlive  time.Duration `json:"keep_alive" yaml:"keep_alive"`
}

// DefaultTCPSocketConfig returns default TCP tuning parameters.
func DefaultTCPSocketConfig() TCPSocketConfig {
	return TCPSocketConfig{
		TTL:        64,
		WindowSize: 65535,
		KeepAlive:  30 * time.Second,
	}
}

// DialWithTuning establishes a TCP connection with custom IP TTL and socket options applied.
func DialWithTuning(ctx context.Context, network, address string, cfg TCPSocketConfig) (*net.TCPConn, error) {
	d := &net.Dialer{
		Timeout:   10 * time.Second,
		KeepAlive: cfg.KeepAlive,
		Control: func(network, address string, c syscall.RawConn) error {
			var syscallErr error
			err := c.Control(func(fd uintptr) {
				if cfg.TTL > 0 {
					// Set IP TTL (IPv4 IP_TTL socket option)
					if err := syscall.SetsockoptInt(int(fd), syscall.IPPROTO_IP, syscall.IP_TTL, cfg.TTL); err != nil {
						syscallErr = err
					}
				}
			})
			if syscallErr != nil {
				return syscallErr
			}
			return err
		},
	}

	conn, err := d.DialContext(ctx, network, address)
	if err != nil {
		return nil, eris.Wrapf(err, "tcp_strategy: dial with tuning to %s", address)
	}

	tcpConn, ok := conn.(*net.TCPConn)
	if !ok {
		_ = conn.Close()
		return nil, eris.New("tcp_strategy: connection is not *net.TCPConn")
	}

	return tcpConn, nil
}

// TCPPayload implements types.FingerprintPayload for TCP fingerprinting.
type TCPPayload struct {
	TTL        int      `json:"ttl"`
	TCPOptions []string `json:"tcp_options"`
}

// PayloadType returns the payload type identifier.
func (p TCPPayload) PayloadType() string { return "tcp_stack" }

// TCPOutputPayload implements types.FingerprintPayload for TCP fingerprinting output.
type TCPOutputPayload struct {
	InferredOS string `json:"inferred_os"`
}

// PayloadType returns the payload type identifier.
func (p TCPOutputPayload) PayloadType() string { return "tcp_stack_output" }

// TCPStrategy implements the FingerprintStrategy for TCP/IP stack fingerprinting (TTL/Window/Options).
type TCPStrategy struct{}

// NewTCPStrategy initializes a new TCPStrategy.
func NewTCPStrategy() *TCPStrategy {
	return &TCPStrategy{}
}

// Name returns the strategy name.
func (s *TCPStrategy) Name() string {
	return "tcp_stack"
}

// Extract performs TCP fingerprinting based on TTL and Options.
func (s *TCPStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	payload, ok := data.Payload.(TCPPayload)
	if !ok {
		return types.FingerprintResult{}, eris.Errorf("tcp_strategy: invalid payload type: %T", data.Payload)
	}

	inferredOS, confidence := s.detectOS(payload.TTL, payload.TCPOptions)

	return types.FingerprintResult{
		Name: s.Name(),
		Data: types.FingerprintData{
			Type:    "tcp_stack",
			Payload: TCPOutputPayload{InferredOS: inferredOS},
		},
		Confidence: confidence,
	}, nil
}

func (s *TCPStrategy) detectOS(ttl int, options []string) (string, float64) {
	switch ttl {
	case 128:
		return s.detectWindows(options)
	case 64:
		return s.detectLinuxMacOS(options)
	case 255:
		return "Network device (Cisco/Juniper)", 0.9
	default:
		return types.UnknownLower, 0.0
	}
}

func (s *TCPStrategy) detectWindows(options []string) (string, float64) {
	for _, opt := range options {
		if opt == "wscale" {
			return "Windows 10/11", 0.85
		}
	}
	return "Windows (older)", 0.7
}

func (s *TCPStrategy) detectLinuxMacOS(options []string) (string, float64) {
	hasTimestamps := false
	hasSack := false
	for _, opt := range options {
		if opt == "timestamps" {
			hasTimestamps = true
		}
		if opt == "sack" {
			hasSack = true
		}
	}

	if hasTimestamps && hasSack {
		return "Linux (modern)", 0.75
	} else if hasTimestamps {
		return "macOS/iOS", 0.7
	}
	return "Linux (older)", 0.5
}

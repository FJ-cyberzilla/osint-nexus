package network

import (
	"net"
	"testing"

	"github.com/stretchr/testify/assert"
)

func setupMockServer(t *testing.T) string {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	assert.NoError(t, err)
	go func() {
		conn, err := ln.Accept()
		if err == nil {
			conn.Close() // Close immediately to force TLS handshake failure
		}
	}()
	return ln.Addr().String()
}

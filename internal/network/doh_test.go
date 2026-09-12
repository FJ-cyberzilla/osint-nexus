package network

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestDoHClient_Resolve(t *testing.T) {
	c := &DoHClient{}
	_, err := c.Resolve(context.Background(), "google.com")
	assert.Error(t, err, "expected error for unresolved doh")
}

func TestDoHClient_FallbackToStandard(t *testing.T) {
	c := &DoHClient{}
	ips, err := c.FallbackToStandard(context.Background(), "google.com")
	assert.NoError(t, err)
	assert.NotEmpty(t, ips)
}

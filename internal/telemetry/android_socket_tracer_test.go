package telemetry

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewAndroidSocketTracer(t *testing.T) {
	// Scenario: Map path does not exist
	tracer, err := NewAndroidSocketTracer("/non/existent/path")
	assert.Error(t, err)
	assert.Nil(t, tracer)
	assert.IsType(t, &BPFMapNotFoundError{}, err)
}

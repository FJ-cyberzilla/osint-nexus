package network

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestDataDropService_Send(t *testing.T) {
	s := &DataDropService{}
	err := s.Send(context.Background(), []byte("test data"))
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not implemented")
}

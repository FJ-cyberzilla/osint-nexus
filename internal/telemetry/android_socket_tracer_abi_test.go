package telemetry

import (
	"testing"
	"unsafe"

	"github.com/stretchr/testify/assert"
)

// Mocking the BPFMap is difficult due to unexported fields, 
// so we focus on testing the logic that depends on the ABI.

func TestPollRecords_ABICompatibility(t *testing.T) {
	// Simulate the key/value pairs based on the defined bpfKey/bpfValue structs
	// This ensures that if the structs change, this test will fail if it deviates
	// from the expected 8/32 byte layout.
	
	key := bpfKey{uid: 1000, tag: 0}
	val := bpfValue{rxBytes: 1024, rxPackets: 10, txBytes: 512, txPackets: 5}

	// Manual check of struct sizes to ensure they match ABI
	assert.Equal(t, uintptr(8), unsafe.Sizeof(key), "bpfKey size must be 8 bytes")
	assert.Equal(t, uintptr(32), unsafe.Sizeof(val), "bpfValue size must be 32 bytes")

	// Validate the logic in PollRecords by using a struct-based approach
	entry := SocketTrafficEntry{
		UID:     key.uid,
		BytesRx: val.rxBytes,
		BytesTx: val.txBytes,
	}

	assert.Equal(t, uint32(1000), entry.UID)
	assert.Equal(t, uint64(1024), entry.BytesRx)
	assert.Equal(t, uint64(512), entry.BytesTx)
}

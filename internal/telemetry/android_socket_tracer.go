package telemetry

import (
	"context"
	"fmt"
	"os"

	"github.com/cilium/ebpf"
)

// AndroidSocketTracer implements EBPFMonitor by reading system-provided BPF maps.
type AndroidSocketTracer struct {
	mapPath string
	bpfMap  *ebpf.Map
}

// NewAndroidSocketTracer initializes a new tracer, ensuring access to the BPF map.
func NewAndroidSocketTracer(mapPath string) (*AndroidSocketTracer, error) {
	if _, err := os.Stat(mapPath); os.IsNotExist(err) {
		return nil, &BPFMapNotFoundError{Path: mapPath}
	}

	bpfMap, err := ebpf.LoadPinnedMap(mapPath, nil)
	if err != nil {
		return nil, fmt.Errorf("telemetry: failed to load pinned BPF map: %w", err)
	}

	return &AndroidSocketTracer{
		mapPath: mapPath,
		bpfMap:  bpfMap,
	}, nil
}

// Key:   struct { uint32 uid; uint32 tag; } (8 bytes)
type bpfKey struct {
	uid uint32
	tag uint32
}

// Value: struct { uint64 rx_bytes; uint64 rx_packets; uint64 tx_bytes; uint64 tx_packets; } (32 bytes)
type bpfValue struct {
	rxBytes   uint64
	rxPackets uint64
	txBytes   uint64
	txPackets uint64
}

// PollRecords iterates over the pinned BPF map and converts raw entries to SocketTrafficEntry.
func (ast *AndroidSocketTracer) PollRecords(ctx context.Context) ([]SocketTrafficEntry, error) {
	var records []SocketTrafficEntry

	iter := ast.bpfMap.Iterate()
	var key bpfKey
	var value bpfValue

	for iter.Next(&key, &value) {
		entry := SocketTrafficEntry{
			UID:     key.uid,
			BytesRx: value.rxBytes,
			BytesTx: value.txBytes,
		}
		records = append(records, entry)
	}

	if err := iter.Err(); err != nil {
		return nil, fmt.Errorf("telemetry: failed to iterate BPF map: %w", err)
	}

	return records, nil
}

// Close releases the underlying BPF map resources.
func (ast *AndroidSocketTracer) Close() error {
	return ast.bpfMap.Close()
}

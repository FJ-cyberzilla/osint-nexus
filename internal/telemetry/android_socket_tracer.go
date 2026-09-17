package telemetry

import (
	"context"
	"encoding/binary"
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

// PollRecords iterates over the pinned BPF map and converts raw entries to SocketTrafficEntry.
func (ast *AndroidSocketTracer) PollRecords(ctx context.Context) ([]SocketTrafficEntry, error) {
	var records []SocketTrafficEntry

	// Android BPF map (e.g., netd's total_stats_map)
	// Key:   struct { uint32 uid; uint32 tag; } (8 bytes)
	// Value: struct { uint64 rx_bytes; uint64 rx_packets; uint64 tx_bytes; uint64 tx_packets; } (32 bytes)
	
	iter := ast.bpfMap.Iterate()
	var key []byte
	var value []byte

	for iter.Next(&key, &value) {
		if len(key) < 8 || len(value) < 32 {
			continue // Skip entries not matching expected ABI
		}

		entry := SocketTrafficEntry{
			UID:     binary.LittleEndian.Uint32(key[0:4]),
			BytesRx: binary.LittleEndian.Uint64(value[0:8]),
			BytesTx: binary.LittleEndian.Uint64(value[16:24]),
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

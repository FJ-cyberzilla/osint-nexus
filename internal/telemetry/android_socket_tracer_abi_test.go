package telemetry

import (
	"testing"
	"unsafe"
)

func TestPollRecords_ABICompatibility(t *testing.T) {
	key := bpfKey{uid: 1000, tag: 0}
	val := bpfValue{rxBytes: 1024, rxPackets: 10, txBytes: 512, txPackets: 5}

	if unsafe.Sizeof(key) != 8 {
		t.Errorf("bpfKey size must be 8 bytes, got %d", unsafe.Sizeof(key))
	}
	if unsafe.Sizeof(val) != 32 {
		t.Errorf("bpfValue size must be 32 bytes, got %d", unsafe.Sizeof(val))
	}

	entry := SocketTrafficEntry{
		UID:     key.uid,
		BytesRx: val.rxBytes,
		BytesTx: val.txBytes,
	}

	if entry.UID != 1000 {
		t.Errorf("expected UID 1000, got %d", entry.UID)
	}
	if entry.BytesRx != 1024 {
		t.Errorf("expected BytesRx 1024, got %d", entry.BytesRx)
	}
	if entry.BytesTx != 512 {
		t.Errorf("expected BytesTx 512, got %d", entry.BytesTx)
	}
}

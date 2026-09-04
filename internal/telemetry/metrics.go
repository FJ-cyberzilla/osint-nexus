package telemetry

import (
	"sync/atomic"
)

// Metrics holds the thread-safe telemetry counters.
type Metrics struct {
	requestsTotal    atomic.Uint64
	requestsSuccess  atomic.Uint64
	requestsFailed   atomic.Uint64
	bytesTransferred atomic.Uint64
}

// MetricsSnapshot represents a serializable state of the metrics.
type MetricsSnapshot struct {
	RequestsTotal    uint64 `json:"requests_total"`
	RequestsSuccess  uint64 `json:"requests_success"`
	RequestsFailed   uint64 `json:"requests_failed"`
	BytesTransferred uint64 `json:"bytes_transferred"`
}

// NewMetrics initializes a new Metrics instance.
func NewMetrics() *Metrics {
	return &Metrics{}
}

// RecordRequest increments the total request counter.
func (m *Metrics) RecordRequest() {
	m.requestsTotal.Add(1)
}

// RecordSuccess increments the successful request counter.
func (m *Metrics) RecordSuccess() {
	m.requestsSuccess.Add(1)
}

// RecordFailure increments the failed request counter.
func (m *Metrics) RecordFailure() {
	m.requestsFailed.Add(1)
}

// RecordBytes adds the number of bytes transferred.
func (m *Metrics) RecordBytes(bytes uint64) {
	m.bytesTransferred.Add(bytes)
}

// Snapshot returns the current state of metrics as a serializable snapshot.
func (m *Metrics) Snapshot() MetricsSnapshot {
	return MetricsSnapshot{
		RequestsTotal:    m.requestsTotal.Load(),
		RequestsSuccess:  m.requestsSuccess.Load(),
		RequestsFailed:   m.requestsFailed.Load(),
		BytesTransferred: m.bytesTransferred.Load(),
	}
}

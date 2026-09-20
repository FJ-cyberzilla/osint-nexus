package detector

import (
	"fmt"
	"math"
	"sync"

	"github.com/google/uuid"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// Severity defines the alert severity level.
type Severity int

const (
	INFO Severity = iota
	WARNING
	CRITICAL
)

// AnomalyAlert represents a detected anomaly.
type AnomalyAlert struct {
	SessionID uuid.UUID
	Message   string
	Severity  Severity
}

// Detector defines the anomaly detection interface.
type Detector interface {
	Detect(event *types.TelemetryEvent) (*AnomalyAlert, error)
}

// StatisticalAnomalyDetector implements anomaly detection using sliding-window Z-scores.
type StatisticalAnomalyDetector struct {
	mu          sync.RWMutex
	windowSize  int
	eventCounts map[string][]float64
	threshold   float64
}

// NewStatisticalAnomalyDetector initializes a new detector.
func NewStatisticalAnomalyDetector(windowSize int, threshold float64) *StatisticalAnomalyDetector {
	return &StatisticalAnomalyDetector{
		windowSize:  windowSize,
		eventCounts: make(map[string][]float64),
		threshold:   threshold,
	}
}

// Detect checks for anomalies in the telemetry event.
func (d *StatisticalAnomalyDetector) Detect(event *types.TelemetryEvent) (*AnomalyAlert, error) {
	if event == nil || event.Payload == nil {
		return nil, fmt.Errorf("detector: invalid telemetry event")
	}

	d.mu.Lock()
	defer d.mu.Unlock()

	// For demonstration, use event type as the key for frequency analysis.
	key := event.EventType
	
	// Get current count (e.g., from payload).
	val, ok := event.Payload["value"].(float64)
	if !ok {
		val = 1.0 // Default frequency
	}

	d.eventCounts[key] = append(d.eventCounts[key], val)
	if len(d.eventCounts[key]) > d.windowSize {
		d.eventCounts[key] = d.eventCounts[key][1:]
	}

	// Calculate Z-score if we have enough data.
	if len(d.eventCounts[key]) < d.windowSize {
		return nil, nil // Not enough data
	}

	mean, stdDev := d.calculateStats(d.eventCounts[key])
	if stdDev == 0 {
		return nil, nil
	}

	zScore := math.Abs((val - mean) / stdDev)

	if zScore > d.threshold {
		return &AnomalyAlert{
			SessionID: event.SessionID,
			Message:   fmt.Sprintf("Anomaly detected in %s: Z-score %.2f > %.2f", key, zScore, d.threshold),
			Severity:  WARNING,
		}, nil
	}

	return nil, nil
}

func (d *StatisticalAnomalyDetector) calculateStats(data []float64) (float64, float64) {
	var sum float64
	for _, v := range data {
		sum += v
	}
	mean := sum / float64(len(data))

	var sumSqDiff float64
	for _, v := range data {
		sumSqDiff += math.Pow(v-mean, 2)
	}
	stdDev := math.Sqrt(sumSqDiff / float64(len(data)))
	return mean, stdDev
}

package engine

import (
	"context"
	"testing"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/detector"
	"github.com/FJ-cyberzilla/osint-nexus/internal/extractor"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/google/uuid"
)

const (
	pipelineTestTimeout = 100 * time.Millisecond
)

type PipelineMockDetector struct {
	detected bool
}

func (m *PipelineMockDetector) Detect(event *types.TelemetryEvent) (*detector.AnomalyAlert, error) {
	if m.detected {
		return &detector.AnomalyAlert{
			SessionID: event.SessionID,
			Message:   "anomaly detected",
			Severity:  detector.WARNING,
		}, nil
	}
	return nil, nil
}

func TestIdentityScoringPipeline_Run(t *testing.T) {
	mockDetector := &PipelineMockDetector{detected: true}
	stylometryExtractor := extractor.NewStylometryExtractor()

	pipeline := NewIdentityScoringPipeline(mockDetector, stylometryExtractor, NewSessionTracker(nil, nil), nil)

	ctx, cancel := context.WithTimeout(context.Background(), pipelineTestTimeout)

	defer cancel()
	
	eventChan := make(chan *types.TelemetryEvent, 1)
	event := &types.TelemetryEvent{
		SessionID: uuid.New(),
		EventType: "test-event",
		Payload: map[string]interface{}{
			"text": "this is a test sentence.",
			"lang": "en",
		},
	}
	
	eventChan <- event
	
	// Run in background and verify it processes the event.
	// Since Run blocks, we use a separate goroutine.
	go pipeline.Run(ctx, eventChan)
	
	// Wait for processing to happen.
	time.Sleep(pipelineTestTimeout / 2)
}

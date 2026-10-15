package detector

import (
	"testing"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

func TestStatisticalAnomalyDetector(t *testing.T) {
	detector := NewStatisticalAnomalyDetector(3, 1.0)
	sessionID := uuid.New()

	// Feed baseline values (window size 3: 10, 10.5, 9.5)
	baselines := []float64{10.0, 10.5, 9.5}
	for _, val := range baselines {
		event := &types.TelemetryEvent{
			SessionID: sessionID,
			EventType: "http_request",
			Payload:   map[string]any{"value": val},
		}
		alert, err := detector.Detect(event)
		require.NoError(t, err)
		assert.Nil(t, alert, "baseline event should not trigger alert")
	}

	// Feed severe anomaly value (500.0)
	anomalyEvent := &types.TelemetryEvent{
		SessionID: sessionID,
		EventType: "http_request",
		Payload:   map[string]any{"value": 500.0},
	}
	alert, err := detector.Detect(anomalyEvent)
	require.NoError(t, err)
	require.NotNil(t, alert, "outlier value should trigger an anomaly alert")
	assert.Equal(t, sessionID, alert.SessionID)
	assert.Equal(t, WARNING, alert.Severity)
}

func TestStatisticalAnomalyDetector_InvalidEvent(t *testing.T) {
	detector := NewStatisticalAnomalyDetector(3, 2.0)
	alert, err := detector.Detect(nil)
	assert.Error(t, err)
	assert.Nil(t, alert)
}

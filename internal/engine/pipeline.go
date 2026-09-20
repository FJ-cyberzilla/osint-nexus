package engine

import (
	"context"
	"fmt"

	"github.com/FJ-cyberzilla/osint-nexus/internal/detector"
	"github.com/FJ-cyberzilla/osint-nexus/internal/extractor"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/FJ-cyberzilla/osint-nexus/internal/ui"
)

// UIMessenger defines the interface for sending updates to the dashboard.
type UIMessenger interface {
	Send(msg any)
}

// IdentityScoringPipeline processes telemetry events.
type IdentityScoringPipeline struct {
	detector  detector.Detector
	extractor *extractor.StylometryExtractor
	tracker   *SessionTracker
	ui        UIMessenger
}

// NewIdentityScoringPipeline initializes the pipeline.
func NewIdentityScoringPipeline(d detector.Detector, e *extractor.StylometryExtractor, t *SessionTracker, ui UIMessenger) *IdentityScoringPipeline {
	return &IdentityScoringPipeline{
		detector:  d,
		extractor: e,
		tracker:   t,
		ui:        ui,
	}
}

// Run processes incoming events.
func (p *IdentityScoringPipeline) Run(ctx context.Context, eventChan <-chan *types.TelemetryEvent) {
	for {
		select {
		case <-ctx.Done():
			return
		case event := <-eventChan:
			// 1. Detect anomalies
			alert, err := p.detector.Detect(event)
			if err != nil {
				if p.ui != nil {
					p.ui.Send(fmt.Sprintf("pipeline error: %v", err))
				}
			}
			if alert != nil && p.ui != nil {
				severity := "INFO"
				switch alert.Severity {
				case detector.WARNING:
					severity = "WARNING"
				case detector.CRITICAL:
					severity = "CRITICAL"
				}
				p.ui.Send(ui.AnomalyAlertMsg{
					SessionID: alert.SessionID.String(),
					Message:   alert.Message,
					Severity:  severity,
				})
			}

			// 2. Extract features (if applicable)
			text, _ := event.Payload["text"].(string)
			lang, _ := event.Payload["lang"].(string)
			if text != "" {
				features, err := p.extractor.Extract(ctx, text, lang)
				if err != nil {
					if p.ui != nil {
						p.ui.Send(fmt.Sprintf("extraction error: %v", err))
					}
				} else if p.ui != nil {
					p.ui.Send(ui.StylometryMsg{
						Language:           features.Language,
						AvgSentenceLength:  features.AvgSentenceLength,
						AvgWordLength:      features.AvgWordLength,
						PunctuationDensity: features.PunctuationDensity,
						VocabularyRichness: features.VocabularyRichness,
					})
				}
			}
		}
	}
}

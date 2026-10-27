package omni_masquerade

import (
	"fmt"
	"time"

	"github.com/rotisserie/eris"
)

// AlgorithmController manages execution flow, pausing, and status reporting for the Omni-Masquerade engine.
type AlgorithmController struct {
	StartTime time.Time
	DebugMode bool
}

// NewAlgorithmController initializes an AlgorithmController.
func NewAlgorithmController(debug bool) *AlgorithmController {
	return &AlgorithmController{
		StartTime: time.Now(),
		DebugMode: debug,
	}
}

// LogProgress logs execution progress if debug mode is enabled.
func (ac *AlgorithmController) LogProgress(format string, args ...interface{}) {
	if ac.DebugMode {
		prefix := fmt.Sprintf("[%s] [OmniMasquerade]", time.Since(ac.StartTime).Truncate(time.Millisecond))
		fmt.Printf("%s %s\n", prefix, fmt.Sprintf(format, args...))
	}
}

// ValidateConfig validates engine configuration parameters.
func ValidateConfig(cfg EngineConfig) error {
	if cfg.MaxWorkers < 0 {
		return eris.New("omni_masquerade: max_workers cannot be negative")
	}
	if cfg.Timeout < 0 {
		return eris.New("omni_masquerade: timeout cannot be negative")
	}
	return nil
}

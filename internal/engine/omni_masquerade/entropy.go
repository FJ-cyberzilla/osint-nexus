package omni_masquerade

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
)

// EntropyInjector injects pseudo-random noise into browser canvas rendering and WebGL parameters to defeat fingerprint correlation.
type EntropyInjector struct {
	noiseFactor float64
}

// NewEntropyInjector initializes a new EntropyInjector.
func NewEntropyInjector(noiseFactor float64) *EntropyInjector {
	if noiseFactor <= 0 {
		noiseFactor = 0.001
	}
	return &EntropyInjector{
		noiseFactor: noiseFactor,
	}
}

// GenerateCanvasNoiseScript returns a JavaScript snippet that overrides HTMLCanvasElement.prototype.toDataURL and WebGLRenderingContext to inject subtle noise.
func (ei *EntropyInjector) GenerateCanvasNoiseScript() string {
	saltBytes := make([]byte, 4)
	_, _ = rand.Read(saltBytes)
	saltHex := hex.EncodeToString(saltBytes)

	return fmt.Sprintf(`
	(function() {
		const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
		HTMLCanvasElement.prototype.toDataURL = function(type) {
			const ctx = this.getContext('2d');
			if (ctx) {
				const imgData = ctx.getImageData(0, 0, this.width, this.height);
				for (let i = 0; i < imgData.data.length; i += 4) {
					// Inject imperceptible micro-noise based on salt %0.2s
					imgData.data[i] = imgData.data[i] ^ (0x%s.charCodeAt(i %% 4) & 1);
				}
				ctx.putImageData(imgData, 0, 0);
			}
			return originalToDataURL.apply(this, arguments);
		};
	})();
	`, saltHex, saltHex)
}

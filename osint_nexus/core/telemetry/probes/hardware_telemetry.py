from typing import Final

ADVANCED_TELEMETRY_JS: Final[str] = """
(async function() {
    const telemetry = {};

    // 1. WebGL Hardware Fingerprinting
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (gl) {
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            telemetry.webgl_vendor = debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'unknown';
            telemetry.webgl_renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown';
        }
    } catch (e) {
        telemetry.webgl_error = e.message;
    }

    // 2. CPU Timing / Performance Anomaly Check
    const start = performance.now();
    for (let i = 0; i < 1000000; i++) {
        Math.sqrt(i);
    }
    telemetry.cpu_benchmark_ms = performance.now() - start;

    // Send payload back to Python via WebViewBridge
    if (window.backendBridge && typeof window.backendBridge.submit_telemetry === 'function') {
        window.backendBridge.submit_telemetry(JSON.stringify(telemetry));
    }
})();
"""

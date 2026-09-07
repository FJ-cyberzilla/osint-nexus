package evasion

import (
	"crypto/rand"
	"math/big"

	"github.com/chromedp/chromedp"
)

// SpoofingOptions defines the configuration for browser fingerprint spoofing.
type SpoofingOptions struct {
	UserAgents []string
}

// GetAllocatorOptions returns the chromedp options for browser spoofing.
func GetAllocatorOptions(opts SpoofingOptions) []chromedp.ExecAllocatorOption {
	if len(opts.UserAgents) == 0 {
		return []chromedp.ExecAllocatorOption{
			chromedp.Flag("headless", true),
			chromedp.Flag("disable-blink-features", "AutomationControlled"),
		}
	}

	var index int64
	n, err := rand.Int(rand.Reader, big.NewInt(int64(len(opts.UserAgents))))
	if err == nil {
		index = n.Int64()
	}

	userAgent := opts.UserAgents[index]
	return []chromedp.ExecAllocatorOption{
		chromedp.Flag("user-agent", userAgent),
		chromedp.Flag("headless", true),
		chromedp.Flag("disable-blink-features", "AutomationControlled"),
	}
}

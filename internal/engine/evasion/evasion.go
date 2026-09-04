package evasion

import (
	"math/rand/v2"

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
	
	userAgent := opts.UserAgents[rand.IntN(len(opts.UserAgents))]
	return []chromedp.ExecAllocatorOption{
		chromedp.Flag("user-agent", userAgent),
		chromedp.Flag("headless", true),
		chromedp.Flag("disable-blink-features", "AutomationControlled"),
	}
}

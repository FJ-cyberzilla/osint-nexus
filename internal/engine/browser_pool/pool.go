package browser_pool

import (
	"context"
	"runtime"
	"strings"
	"sync"
	"time"

	"github.com/chromedp/cdproto/network"
	"github.com/chromedp/chromedp"
	"github.com/rotisserie/eris"
)

// DefaultTaskTimeout is the default execution timeout for browser tasks.
const DefaultTaskTimeout = 30 * time.Second

// DefaultCloudflareCheckInterval is the polling interval when checking for Cloudflare challenges.
const DefaultCloudflareCheckInterval = 1 * time.Second

// ErrCloudflareBlocked indicates that a browser navigation was permanently blocked or timed out by a Cloudflare anti-bot challenge.
var ErrCloudflareBlocked = eris.New("browser_pool: cloudflare challenge blocked or timeout")

// BrowserInstance wraps a context and cancel function for a managed browser session.
type BrowserInstance struct {
	Ctx    context.Context
	Cancel context.CancelFunc
}

// Pool manages a pool of browser instances to optimize resource utilization.
type Pool struct {
	opts    []chromedp.ExecAllocatorOption
	pool    chan *BrowserInstance
	mu      sync.Mutex
	closing bool
}

// NewPool initializes a new Pool with the specified capacity and allocator options.
func NewPool(capacity int, opts ...chromedp.ExecAllocatorOption) *Pool {
	return &Pool{
		opts: opts,
		pool: make(chan *BrowserInstance, capacity),
	}
}

// DefaultAllocatorOptions returns robust production-grade allocator options for stealth, stability, and GitHub Actions support.
func DefaultAllocatorOptions() []chromedp.ExecAllocatorOption {
	return []chromedp.ExecAllocatorOption{
		chromedp.NoSandbox,
		chromedp.DisableGPU,
		chromedp.WindowSize(1920, 1080),
		chromedp.UserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
		chromedp.Flag("disable-dev-shm-usage", true),
		chromedp.Flag("blink-settings", "imagesEnabled=false"),
	}
}

// SetupLowNetworkRules blocks heavy network assets (images, media, fonts, stylesheets) to save bandwidth.
func SetupLowNetworkRules(ctx context.Context) error {
	if err := chromedp.Run(ctx, network.Enable()); err != nil {
		return eris.Wrap(err, "browser_pool: enable network domain")
	}

	blockedURLs := []string{
		"*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg",
		"*.css", "*.woff", "*.woff2", "*.ttf", "*.ico",
		"*ads*", "*tracker*", "*analytics*",
	}

	patterns := make([]*network.BlockPattern, 0, len(blockedURLs))
	for _, u := range blockedURLs {
		patterns = append(patterns, &network.BlockPattern{
			URLPattern: u,
			Block:      true,
		})
	}

	if err := chromedp.Run(ctx, network.SetBlockedURLs().WithURLPatterns(patterns)); err != nil {
		return eris.Wrap(err, "browser_pool: set blocked urls")
	}

	return nil
}

// WaitForCloudflare polls the page title until Cloudflare anti-bot challenge indicators ("Just a moment...", "Attention Required!") disappear or context expires.
func WaitForCloudflare(ctx context.Context, checkInterval time.Duration) error {
	if checkInterval <= 0 {
		checkInterval = DefaultCloudflareCheckInterval
	}

	ticker := time.NewTicker(checkInterval)
	defer ticker.Stop()

	var title string
	for {
		select {
		case <-ctx.Done():
			return eris.Wrap(ctx.Err(), "browser_pool: cloudflare wait context expired")
		case <-ticker.C:
			if err := chromedp.Run(ctx, chromedp.Title(&title)); err != nil {
				return eris.Wrap(err, "browser_pool: failed to fetch page title during cloudflare check")
			}

			if !strings.Contains(title, "Just a moment...") && !strings.Contains(title, "Attention Required!") {
				return nil
			}
		}
	}
}

// Get acquires a browser instance from the pool or creates a new one if necessary.
func (p *Pool) Get(ctx context.Context) (*BrowserInstance, error) {
	select {
	case instance := <-p.pool:
		return instance, nil
	default:
		return p.createInstance(ctx)
	}
}

// Put returns a browser instance to the pool.
func (p *Pool) Put(instance *BrowserInstance) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.closing {
		instance.Cancel()
		return
	}

	select {
	case p.pool <- instance:
	default:
		instance.Cancel()
	}
}

// createInstance initializes a new managed browser context.
func (p *Pool) createInstance(ctx context.Context) (*BrowserInstance, error) {
	allocOpts := p.opts
	if len(allocOpts) == 0 {
		allocOpts = DefaultAllocatorOptions()
	}

	allocCtx, cancel := chromedp.NewExecAllocator(ctx, allocOpts...)
	browserCtx, browserCancel := chromedp.NewContext(allocCtx)

	if err := chromedp.Run(browserCtx); err != nil {
		browserCancel()
		cancel()
		return nil, eris.Wrap(err, "browser_pool: create instance")
	}

	return &BrowserInstance{
		Ctx: browserCtx,
		Cancel: func() {
			browserCancel()
			cancel()
		},
	}, nil
}

// ExecuteTask runs a task within an isolated tab session with timeout and low network optimization.
func (p *Pool) ExecuteTask(ctx context.Context, targetURL string, timeout time.Duration, taskFn func(tabCtx context.Context) error) error {
	instance, err := p.Get(ctx)
	if err != nil {
		return eris.Wrap(err, "browser_pool: acquire instance for task")
	}
	defer p.Put(instance)

	tabCtx, tabCancel := chromedp.NewContext(instance.Ctx)
	defer tabCancel()

	if timeout <= 0 {
		timeout = DefaultTaskTimeout
	}

	timeoutCtx, timeoutCancel := context.WithTimeout(tabCtx, timeout)
	defer timeoutCancel()

	if err := SetupLowNetworkRules(timeoutCtx); err != nil {
		return eris.Wrap(err, "browser_pool: setup low network rules")
	}

	return taskFn(timeoutCtx)
}

// RunWorkerPool executes tasks concurrently across the pool using worker budgeting based on CPU cores.
func (p *Pool) RunWorkerPool(ctx context.Context, urls []string, maxWorkers int, taskFn func(ctx context.Context, url string) error) map[string]error {
	if maxWorkers <= 0 {
		maxWorkers = runtime.NumCPU() - 1
		if maxWorkers < 1 {
			maxWorkers = 1
		}
	}

	urlChan := make(chan string, len(urls))
	for _, u := range urls {
		urlChan <- u
	}
	close(urlChan)

	var wg sync.WaitGroup
	semaphore := make(chan struct{}, maxWorkers)

	var errMu sync.Mutex
	errorsMap := make(map[string]error)

	for url := range urlChan {
		wg.Add(1)
		semaphore <- struct{}{}

		go func(targetURL string) {
			defer wg.Done()
			defer func() { <-semaphore }()

			err := p.ExecuteTask(ctx, targetURL, DefaultTaskTimeout, func(tabCtx context.Context) error {
				if err := chromedp.Run(tabCtx, chromedp.Navigate(targetURL)); err != nil {
					return eris.Wrapf(err, "navigate to %s", targetURL)
				}
				return taskFn(tabCtx, targetURL)
			})

			if err != nil {
				errMu.Lock()
				errorsMap[targetURL] = err
				errMu.Unlock()
			}
		}(url)
	}

	wg.Wait()
	return errorsMap
}

// Close gracefully shuts down all instances in the pool.
func (p *Pool) Close() {
	p.mu.Lock()
	p.closing = true
	p.mu.Unlock()

	close(p.pool)
	for instance := range p.pool {
		instance.Cancel()
	}
}

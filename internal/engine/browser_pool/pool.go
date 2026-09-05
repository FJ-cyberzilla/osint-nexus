package browser_pool

import (
	"context"
	"fmt"
	"sync"

	"github.com/chromedp/chromedp"
)

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

// Get acquires a browser instance from the pool or creates a new one if necessary.
func (p *Pool) Get(ctx context.Context) (*BrowserInstance, error) {
	select {
	case instance := <-p.pool:
		return instance, nil
	default:
		// Pool is empty, create new instance
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
		// Pool full, close instance
		instance.Cancel()
	}
}

// createInstance initializes a new managed browser context.
func (p *Pool) createInstance(ctx context.Context) (*BrowserInstance, error) {
	allocCtx, cancel := chromedp.NewExecAllocator(ctx, p.opts...)
	browserCtx, browserCancel := chromedp.NewContext(allocCtx)

	// Ensure the browser is started
	if err := chromedp.Run(browserCtx); err != nil {
		cancel()
		browserCancel()
		return nil, fmt.Errorf("browser_pool: create instance: %w", err)
	}

	return &BrowserInstance{
		Ctx: browserCtx,
		Cancel: func() {
			browserCancel()
			cancel()
		},
	}, nil
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

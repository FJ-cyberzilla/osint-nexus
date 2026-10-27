package browser_pool

import (
	"context"
	"os"
	"os/exec"
	"testing"
	"time"

	"github.com/chromedp/chromedp"
)

func TestPool(t *testing.T) {
	// Skip in Termux or CI environments to prevent crashes
	if os.Getenv("TERMUX_VERSION") != "" || os.Getenv("CI") != "" {
		t.Skip("skipping browser pool tests in restricted environment (Termux/CI)")
	}

	if _, err := exec.LookPath("google-chrome"); err != nil {
		t.Skip("google-chrome not found, skipping TestPool")
	}

	pool := NewPool(2)
	defer pool.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	instance, err := pool.Get(ctx)
	if err != nil {
		t.Fatalf("failed to get instance: %v", err)
	}

	// Verify instance works
	err = chromedp.Run(instance.Ctx, chromedp.Navigate("about:blank"))
	if err != nil {
		t.Errorf("failed to navigate: %v", err)
	}

	pool.Put(instance)

	// Get again
	instance2, err := pool.Get(ctx)
	if err != nil {
		t.Fatalf("failed to get instance again: %v", err)
	}
	if instance2 != instance {
		t.Error("expected same instance from pool")
	}
	pool.Put(instance2)
}

func TestWaitForCloudflareTimeout(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	err := WaitForCloudflare(ctx, 10*time.Millisecond)
	if err == nil {
		t.Error("expected error due to context timeout, got nil")
	}
}

func TestRunWorkerPoolEmpty(t *testing.T) {
	pool := NewPool(1)
	defer pool.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	errs := pool.RunWorkerPool(ctx, []string{}, 2, func(tabCtx context.Context, url string) error {
		return nil
	})

	if len(errs) != 0 {
		t.Errorf("expected 0 errors for empty url list, got %d", len(errs))
	}
}

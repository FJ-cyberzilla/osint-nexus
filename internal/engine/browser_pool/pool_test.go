package browser_pool

import (
	"context"
	"os/exec"
	"testing"
	"time"

	"github.com/chromedp/chromedp"
)

func TestPool(t *testing.T) {
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

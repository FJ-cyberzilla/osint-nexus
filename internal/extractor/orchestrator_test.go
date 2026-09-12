package extractor

import (
	"context"
	"testing"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"golang.org/x/net/html"
)

type mockExtractor struct {
	pivots *types.ExtractedPivots
}

func (m *mockExtractor) Extract(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	return m.pivots, nil
}

type mockStreamExtractor struct {
	pivots *types.ExtractedPivots
}

func (m *mockStreamExtractor) Extract(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	return m.pivots, nil
}

func (m *mockStreamExtractor) HandleToken(token html.Token) {}
func (m *mockStreamExtractor) HandleText(text string)      {}
func (m *mockStreamExtractor) GetPivots() *types.ExtractedPivots {
	return m.pivots
}

func TestOrchestrator_Extract_Fallback(t *testing.T) {
	m1 := &mockExtractor{pivots: &types.ExtractedPivots{Emails: []string{"test1@example.com"}}}
	m2 := &mockExtractor{pivots: &types.ExtractedPivots{Emails: []string{"test2@example.com"}}}
	o := NewOrchestrator(m1, m2)

	pivots, err := o.Extract(context.Background(), "<html></html>")
	if err != nil {
		t.Fatalf("Extract failed: %v", err)
	}

	if len(pivots.Emails) != 2 {
		t.Errorf("Expected 2 emails, got %d", len(pivots.Emails))
	}
}

func TestOrchestrator_Extract_Streaming(t *testing.T) {
	m1 := &mockStreamExtractor{pivots: &types.ExtractedPivots{Emails: []string{"test1@example.com"}}}
	m2 := &mockStreamExtractor{pivots: &types.ExtractedPivots{Emails: []string{"test2@example.com"}}}
	o := NewOrchestrator(m1, m2)

	pivots, err := o.Extract(context.Background(), "<html></html>")
	if err != nil {
		t.Fatalf("Extract failed: %v", err)
	}

	if len(pivots.Emails) != 2 {
		t.Errorf("Expected 2 emails, got %d", len(pivots.Emails))
	}
}

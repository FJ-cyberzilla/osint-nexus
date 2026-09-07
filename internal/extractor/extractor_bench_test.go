package extractor

import (
	"context"
	"strings"
	"testing"

	"github.com/PuerkitoBio/goquery"
	"github.com/osint-nexus/internal/types"
)

// Sample HTML for benchmarking
const sampleHTML = `
<html>
<body>
	<h1>Profile</h1>
	<p>Bio description here.</p>
	<a href="https://twitter.com/jdoe">Twitter</a>
	<a href="https://github.com/jdoe">GitHub</a>
	<a href="mailto:jdoe@example.com">Email</a>
	<meta name="description" content="This is a bio description for jdoe.">
</body>
</html>
`

// Old monolithic approach simulation (GoQuery)
func benchmarkGoQuery(htmlContent string) {
	doc, _ := goquery.NewDocumentFromReader(strings.NewReader(htmlContent))
	doc.Find("a").Each(func(i int, s *goquery.Selection) {
		_ = s.AttrOr("href", "")
	})
	_ = doc.Find("meta[name='description']").AttrOr("content", "")
}

func BenchmarkOrchestrator_Streaming(b *testing.B) {
	cfg := types.NewDefaultConfig()
	pgpExt, _ := NewPGPExtractor()
	emailExt, _ := NewEmailExtractor()
	orchestrator := NewOrchestrator(
		emailExt,
		NewMetaExtractor(),
		NewSocialExtractor(cfg),
		pgpExt,
	)
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = orchestrator.Extract(ctx, sampleHTML)
	}
}

func BenchmarkOrchestrator_GoQuery(b *testing.B) {
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		benchmarkGoQuery(sampleHTML)
	}
}

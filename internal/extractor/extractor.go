package extractor

import (
	"context"
	"fmt"
	"net/url"
	"regexp"
	"strings"

	"github.com/PuerkitoBio/goquery"
	"github.com/osint-nexus/internal/types"
)

// PivotExtractor coordinates regex and HTML parsing engines.
type PivotExtractor struct {
	emailRegex    *regexp.Regexp
	pgpRegex      *regexp.Regexp
	telegramRegex *regexp.Regexp
}

// NewPivotExtractor initializes and returns a fully configured PivotExtractor.
func NewPivotExtractor() (*PivotExtractor, error) {
	emailPattern, err := regexp.Compile(`(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}`)
	if err != nil {
		return nil, fmt.Errorf("pivot_extractor: compile email regex: %w", err)
	}

	pgpPattern, err := regexp.Compile(`-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----`)
	if err != nil {
		return nil, fmt.Errorf("pivot_extractor: compile pgp regex: %w", err)
	}

	telegramPattern, err := regexp.Compile(`(?i)t\.me/([a-z0-9_]{5,32})`)
	if err != nil {
		return nil, fmt.Errorf("pivot_extractor: compile telegram regex: %w", err)
	}

	return &PivotExtractor{
		emailRegex:    emailPattern,
		pgpRegex:      pgpPattern,
		telegramRegex: telegramPattern,
	}, nil
}

// Extract parses the HTML content and returns harvested pivots.
func (p *PivotExtractor) Extract(ctx context.Context, rawHTML string, sourceURL string) (*types.ExtractedPivots, error) {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(rawHTML))
	if err != nil {
		return nil, fmt.Errorf("pivot_extractor: parse html: %w", err)
	}

	emails := p.extractEmails(rawHTML, doc)
	pgpKeys := p.extractPGPKeys(rawHTML)
	links, handles := p.extractLinksAndHandles(doc, sourceURL)
	bio := p.extractBio(doc)

	return &types.ExtractedPivots{
		Emails:        emails,
		PGPKeys:       pgpKeys,
		ExternalLinks: links,
		SocialHandles: handles,
		Bio:           &bio,
	}, nil
}

func (p *PivotExtractor) extractEmails(rawHTML string, doc *goquery.Document) []string {
	emailSet := make(map[string]struct{})

	// Regex extraction
	matches := p.emailRegex.FindAllString(rawHTML, -1)
	for _, m := range matches {
		emailSet[m] = struct{}{}
	}

	// Mailto extraction
	doc.Find("a[href^='mailto:']").Each(func(i int, s *goquery.Selection) {
		href, _ := s.Attr("href")
		email := strings.TrimPrefix(href, "mailto:")
		email = strings.Split(email, "?")[0]
		if p.emailRegex.MatchString(email) {
			emailSet[email] = struct{}{}
		}
	})

	emails := make([]string, 0, len(emailSet))
	for e := range emailSet {
		emails = append(emails, e)
	}
	return emails
}

func (p *PivotExtractor) extractPGPKeys(rawHTML string) []string {
	return p.pgpRegex.FindAllString(rawHTML, -1)
}

func (p *PivotExtractor) extractLinksAndHandles(doc *goquery.Document, sourceURL string) ([]string, []types.SocialHandle) {
	u, _ := url.Parse(sourceURL)
	sourceDomain := ""
	if u != nil {
		sourceDomain = strings.ToLower(u.Host)
	}

	linkSet := make(map[string]struct{})
	var socialHandles []types.SocialHandle

	doc.Find("a[href]").Each(func(i int, s *goquery.Selection) {
		href, _ := s.Attr("href")
		if !strings.HasPrefix(href, "http://") && !strings.HasPrefix(href, "https://") {
			return
		}

		parsed, err := url.Parse(href)
		if err != nil {
			return
		}

		hrefDomain := strings.ToLower(parsed.Host)
		if sourceDomain != "" && (hrefDomain == sourceDomain || strings.HasSuffix(hrefDomain, "."+sourceDomain)) {
			return
		}

		linkSet[href] = struct{}{}

		// Simple handle detection
		platform, username := p.identifySocial(hrefDomain, parsed.Path)
		if platform != "" {
			socialHandles = append(socialHandles, types.SocialHandle{
				Platform: platform,
				Username: username,
				URL:      href,
			})
		}
	})

	links := make([]string, 0, len(linkSet))
	for l := range linkSet {
		links = append(links, l)
	}
	return links, socialHandles
}

func (p *PivotExtractor) identifySocial(domain, path string) (string, string) {
	platforms := map[string]string{
		"twitter.com":   "Twitter",
		"x.com":         "Twitter",
		"instagram.com": "Instagram",
		"linkedin.com":  "LinkedIn",
		"github.com":    "GitHub",
		"t.me":          "Telegram",
	}

	platform := ""
	for dom, name := range platforms {
		if domain == dom || strings.HasSuffix(domain, "."+dom) {
			platform = name
			break
		}
	}

	if platform == "" {
		return "", ""
	}

	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) > 0 && parts[0] != "" {
		ignored := map[string]bool{"share": true, "home": true, "intent": true, "search": true, "p": true}
		if !ignored[parts[0]] {
			return platform, parts[0]
		}
	}

	return "", ""
}

func (p *PivotExtractor) extractBio(doc *goquery.Document) string {
	selectors := []string{
		"meta[name='description']",
		"meta[property='og:description']",
		"meta[property='twitter:description']",
	}
	for _, sel := range selectors {
		if content, exists := doc.Find(sel).Attr("content"); exists {
			return strings.TrimSpace(content)
		}
	}
	// Fallback to text content if meta descriptions are absent
	bio := doc.Find("div[class*='bio'], div[class*='description'], p").First().Text()
	return strings.TrimSpace(bio)
}

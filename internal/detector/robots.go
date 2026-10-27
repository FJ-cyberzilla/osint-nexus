package detector

import (
	"bufio"
	"context"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/rotisserie/eris"
)

const (
	DefaultUserAgent = "OSINT-Nexus-Bot/1.0"
	DefaultTimeout   = 5 * time.Second
)

// RobotsRule holds parsed allow/disallow rules for a user agent.
type RobotsRule struct {
	UserAgent    string
	Disallowed   []string
	Allowed      []string
	CrawlDelay   time.Duration
}

// RobotsParser parses and evaluates robots.txt rules for target domains.
type RobotsParser struct {
	httpClient *http.Client
}

// NewRobotsParser initializes a new RobotsParser.
func NewRobotsParser() *RobotsParser {
	return &RobotsParser{
		httpClient: &http.Client{
			Timeout: DefaultTimeout,
		},
	}
}

// FetchAndParse fetches robots.txt from target base URL and parses rules.
func (p *RobotsParser) FetchAndParse(ctx context.Context, targetURL string) (*RobotsRule, error) {
	parsedURL, err := url.Parse(targetURL)
	if err != nil {
		return nil, eris.Wrapf(err, "robots_parser: invalid target URL: %s", targetURL)
	}

	robotsURL := fmt.Sprintf("%s://%s/robots.txt", parsedURL.Scheme, parsedURL.Host)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, robotsURL, nil)
	if err != nil {
		return nil, eris.Wrap(err, "robots_parser: create request")
	}
	req.Header.Set("User-Agent", DefaultUserAgent)

	resp, err := p.httpClient.Do(req)
	if err != nil {
		// If robots.txt cannot be fetched (e.g. 404 or connection error), default to allowing all
		return &RobotsRule{UserAgent: "*", Disallowed: []string{}, Allowed: []string{}}, nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return &RobotsRule{UserAgent: "*", Disallowed: []string{}, Allowed: []string{}}, nil
	}

	rule := &RobotsRule{UserAgent: "*"}
	scanner := bufio.NewScanner(resp.Body)
	currentUserAgent := ""

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			continue
		}

		key := strings.TrimSpace(strings.ToLower(parts[0]))
		val := strings.TrimSpace(parts[1])

		switch key {
		case "user-agent":
			currentUserAgent = val
		case "disallow":
			if currentUserAgent == "*" || strings.Contains(strings.ToLower(currentUserAgent), "osint") {
				rule.Disallowed = append(rule.Disallowed, val)
			}
		case "allow":
			if currentUserAgent == "*" || strings.Contains(strings.ToLower(currentUserAgent), "osint") {
				rule.Allowed = append(rule.Allowed, val)
			}
		case "crawl-delay":
			if parsedDelay, parseErr := time.ParseDuration(val + "s"); parseErr == nil {
				rule.CrawlDelay = parsedDelay
			}
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, eris.Wrap(err, "robots_parser: scan robots.txt")
	}

	return rule, nil
}

// IsAllowed evaluates whether a specific path is permitted under robots.txt rules.
func (r *RobotsRule) IsAllowed(path string) bool {
	for _, disallow := range r.Disallowed {
		if disallow != "" && strings.HasPrefix(path, disallow) {
			// Check if specifically allowed override exists
			for _, allow := range r.Allowed {
				if allow != "" && strings.HasPrefix(path, allow) {
					return true
				}
			}
			return false
		}
	}
	return true
}

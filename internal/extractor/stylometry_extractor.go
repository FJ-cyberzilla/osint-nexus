package extractor

import (
	"context"
	"regexp"
	"strings"
)

// LanguageMarkers defines sets of markers for different languages.
type LanguageMarkers struct {
	Punctuation *regexp.Regexp
	SentDelim   *regexp.Regexp
}

var languageBank = map[string]LanguageMarkers{
	"en": {
		Punctuation: regexp.MustCompile(`[[:punct:]]`),
		SentDelim:   regexp.MustCompile(`[.!?]`),
	},
	"fa": {
		Punctuation: regexp.MustCompile("[\u060C\u061B\u061F\u0640\u066A\u066B\u066C]"), // Persian punct
		SentDelim:   regexp.MustCompile("[\u002E\u06D4]"),                              // Full stop, Persian full stop
	},
	"tr": {
		Punctuation: regexp.MustCompile(`[[:punct:]]`),
		SentDelim:   regexp.MustCompile(`[.!?]`),
	},
}

// StylometricFeatures holds the calculated behavioral markers.
type StylometricFeatures struct {
	Language           string
	AvgSentenceLength  float64
	AvgWordLength      float64
	PunctuationDensity float64
	VocabularyRichness float64
}

// StylometryExtractor calculates behavioral metrics from text with language support.
type StylometryExtractor struct{}

// NewStylometryExtractor initializes a new extractor.
func NewStylometryExtractor() *StylometryExtractor {
	return &StylometryExtractor{}
}

// Extract calculates stylometric features from the input text, defaulting to English if language not supported.
func (e *StylometryExtractor) Extract(ctx context.Context, text string, lang string) (*StylometricFeatures, error) {
	markers, ok := languageBank[lang]
	if !ok {
		markers = languageBank["en"]
		lang = "en"
	}

	words := strings.Fields(text)
	sentences := markers.SentDelim.Split(text, -1)
	
	wordCount := float64(len(words))
	if wordCount == 0 {
		return &StylometricFeatures{Language: lang}, nil
	}

	var totalWordLength float64
	for _, word := range words {
		totalWordLength += float64(len(word))
	}

	punctuation := float64(len(markers.Punctuation.FindAllString(text, -1)))

	uniqueWords := make(map[string]bool)
	for _, word := range words {
		uniqueWords[strings.ToLower(word)] = true
	}

	return &StylometricFeatures{
		Language:           lang,
		AvgSentenceLength:  wordCount / float64(len(sentences)),
		AvgWordLength:     totalWordLength / wordCount,
		PunctuationDensity: punctuation / float64(len(text)),
		VocabularyRichness: float64(len(uniqueWords)) / wordCount,
	}, nil
}

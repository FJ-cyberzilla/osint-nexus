package types

import "time"

type ScanResult struct {
	ID        int       `json:"id"`
	Username  string    `json:"username"`
	Platform  string    `json:"platform"`
	Found     bool      `json:"found"`
	Timestamp time.Time `json:"timestamp"`
}

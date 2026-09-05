package types

type IOCType string

const (
	IOCTypeIPv4   IOCType = "ipv4"
	IOCTypeDomain IOCType = "domain"
	IOCTypeSHA256 IOCType = "sha256"
	IOCTypeMD5    IOCType = "md5"
	IOCTypeEmail  IOCType = "email"
)

type ExtractedIOC struct {
	Type  IOCType `json:"type"`
	Value string  `json:"value"`
}

type SocialHandle struct {
	Platform string `json:"platform"`
	Username string `json:"username"`
	URL      string `json:"url"`
}

type PlatformIdentity struct {
	Platform string `json:"platform"`
	Username string `json:"username"`
}

type LinkHarvestResult struct {
	ExternalLinks []string       `json:"external_links"`
	SocialHandles []SocialHandle `json:"social_handles"`
}

type ExtractedPivots struct {
	Emails        []string       `json:"emails"`
	PGPKeys       []string       `json:"pgp_keys"`
	ExternalLinks []string       `json:"external_links"`
	SocialHandles []SocialHandle `json:"social_handles"`
	Bio           *string        `json:"bio"`
}

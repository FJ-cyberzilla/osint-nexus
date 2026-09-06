package config

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/spf13/viper"
)

// Project-wide UI & Core Metadata Constants
const (
	Version     = "4.1.1"
	ColorOrange = "bold orange1"
	ColorTip    = "yellow"
)

// DeviceInference Constants
const (
	DeviceUnidentified   = "Unidentified"
	DeviceUnknown        = "Unknown"
	MinConfidence        = 0.0
	MaxConfidence        = 1.0
	RegexMatchConfidence = 0.8
)

// Fallback System Configuration Defaults
const (
	DefaultAppName           = "OSINT-Nexus"
	DefaultEnvironment       = "production"
	DefaultLogLevel          = "info"
	DefaultConcurrency       = 50
	DefaultTimeoutSeconds    = 10
	DefaultMaxRetries        = 3
	DefaultJitterMin         = 1.0
	DefaultJitterMax         = 3.0
	DefaultBackoffFactor     = 0.5
	DefaultUserAgent         = "OSINT-Nexus/4.1.1 (+https://github.com/FJ-cyberzilla/osint-nexus)"
	DefaultDBDriver          = "sqlite3"
	DefaultDBPath            = "./data/nexus.db"
	DefaultDNSLeakPrevention = true
	DefaultUseProxies        = false
	DefaultBrowserPoolSize   = 5
	DefaultGitHubRateLimit   = 60
	DefaultTwitterRateLimit  = 30
)

// Config represents the top-level configuration schema.
type Config struct {
	App      AppConfig      `mapstructure:"app"`
	Engine   EngineConfig   `mapstructure:"engine"`
	Database DatabaseConfig `mapstructure:"database"`
	Evasion  EvasionConfig  `mapstructure:"evasion"`
	Provider ProviderConfig `mapstructure:"providers"`
}

type AppConfig struct {
	Name        string `mapstructure:"name"`
	Environment string `mapstructure:"environment"`
	LogLevel    string `mapstructure:"log_level"`
}

type EngineConfig struct {
	Concurrency    int           `mapstructure:"concurrency"`
	TimeoutSeconds time.Duration `mapstructure:"timeout_seconds"`
	MaxRetries     int           `mapstructure:"max_retries"`
	JitterMin      float64       `mapstructure:"jitter_min"`
	JitterMax      float64       `mapstructure:"jitter_max"`
	BackoffFactor  float64       `mapstructure:"backoff_factor"`
	UserAgent      string        `mapstructure:"user_agent"`
}

type DatabaseConfig struct {
	Driver      string `mapstructure:"driver"`
	Path        string `mapstructure:"path"`
	AutoMigrate bool   `mapstructure:"auto_migrate"`
}

type EvasionConfig struct {
	DNSLeakPrevention bool     `mapstructure:"dns_leak_prevention"`
	UseProxies        bool     `mapstructure:"use_proxies"`
	ProxyList         []string `mapstructure:"proxy_list"`
	BrowserPoolSize   int      `mapstructure:"browser_pool_size"`
}

type ProviderSetting struct {
	Enabled         bool `mapstructure:"enabled"`
	RateLimitPerMin int  `mapstructure:"rate_limit_per_min"`
}

type ProviderConfig struct {
	GitHub    ProviderSetting `mapstructure:"github"`
	Twitter   ProviderSetting `mapstructure:"twitter"`
	Instagram ProviderSetting `mapstructure:"instagram"`
	Aparat    ProviderSetting `mapstructure:"aparat"`
	Fingerbank ProviderSetting `mapstructure:"fingerbank"`
}

var (
	instance *Config
	once     sync.Once
)

// LoadConfig initializes Viper, sets defaults, parses config.yaml,
// and maps environment variables prefixed with OSINT_.
func LoadConfig(configPath string) (*Config, error) {
	once.Do(func() {
		v := viper.New()

		// 1. Populate Viper defaults from compile-time constants
		setConstantDefaults(v)

		// 2. Map environment variable overrides (e.g. OSINT_ENGINE_CONCURRENCY=100)
		v.SetEnvPrefix("OSINT")
		v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
		v.AutomaticEnv()

		// 3. Configure file discovery
		if configPath != "" {
			v.SetConfigFile(configPath)
		} else {
			v.AddConfigPath("./configs")
			v.AddConfigPath(".")
			v.SetConfigName("config")
			v.SetConfigType("yaml")
		}

		// 4. Attempt reading YAML config (silent fallback if missing)
		_ = v.ReadInConfig()

		var cfg Config
		if err := v.Unmarshal(&cfg); err != nil {
			// Fallback directly to struct populated with default constants
			cfg = buildFallbackConfig()
		} else {
			cfg.Engine.TimeoutSeconds = cfg.Engine.TimeoutSeconds * time.Second
		}

		instance = &cfg
	})

	return instance, nil
}

// Get returns the initialized configuration singleton.
func Get() *Config {
	if instance == nil {
		if _, err := LoadConfig(""); err != nil {
			panic(fmt.Errorf("config not initialized: %w", err))
		}
	}
	return instance
}

func setConstantDefaults(v *viper.Viper) {
	v.SetDefault("app.name", DefaultAppName)
	v.SetDefault("app.environment", DefaultEnvironment)
	v.SetDefault("app.log_level", DefaultLogLevel)

	v.SetDefault("engine.concurrency", DefaultConcurrency)
	v.SetDefault("engine.timeout_seconds", DefaultTimeoutSeconds)
	v.SetDefault("engine.max_retries", DefaultMaxRetries)
	v.SetDefault("engine.jitter_min", DefaultJitterMin)
	v.SetDefault("engine.jitter_max", DefaultJitterMax)
	v.SetDefault("engine.backoff_factor", DefaultBackoffFactor)
	v.SetDefault("engine.user_agent", DefaultUserAgent)

	v.SetDefault("database.driver", DefaultDBDriver)
	v.SetDefault("database.path", DefaultDBPath)
	v.SetDefault("database.auto_migrate", true)

	v.SetDefault("evasion.dns_leak_prevention", DefaultDNSLeakPrevention)
	v.SetDefault("evasion.use_proxies", DefaultUseProxies)
	v.SetDefault("evasion.browser_pool_size", DefaultBrowserPoolSize)

	v.SetDefault("providers.github.enabled", true)
	v.SetDefault("providers.github.rate_limit_per_min", DefaultGitHubRateLimit)
	v.SetDefault("providers.twitter.enabled", true)
	v.SetDefault("providers.twitter.rate_limit_per_min", DefaultTwitterRateLimit)
	v.SetDefault("providers.fingerbank.enabled", false)
	v.SetDefault("providers.fingerbank.rate_limit_per_min", 60)
}

func buildFallbackConfig() Config {
	return Config{
		App: AppConfig{
			Name:        DefaultAppName,
			Environment: DefaultEnvironment,
			LogLevel:    DefaultLogLevel,
		},
		Engine: EngineConfig{
			Concurrency:    DefaultConcurrency,
			TimeoutSeconds: time.Duration(DefaultTimeoutSeconds) * time.Second,
			MaxRetries:     DefaultMaxRetries,
			JitterMin:      DefaultJitterMin,
			JitterMax:      DefaultJitterMax,
			BackoffFactor:  DefaultBackoffFactor,
			UserAgent:      DefaultUserAgent,
		},
		Database: DatabaseConfig{
			Driver:      DefaultDBDriver,
			Path:        DefaultDBPath,
			AutoMigrate: true,
		},
		Evasion: EvasionConfig{
			DNSLeakPrevention: DefaultDNSLeakPrevention,
			UseProxies:        DefaultUseProxies,
			BrowserPoolSize:   DefaultBrowserPoolSize,
		},
		Provider: ProviderConfig{
			GitHub:  ProviderSetting{Enabled: true, RateLimitPerMin: DefaultGitHubRateLimit},
			Twitter: ProviderSetting{Enabled: true, RateLimitPerMin: DefaultTwitterRateLimit},
		},
	}
}

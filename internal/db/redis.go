package db

import (
	"context"
	"fmt"

	"github.com/redis/go-redis/v9"
)

// RedisClient wraps the redis client.
type RedisClient struct {
	client *redis.Client
}

// NewRedisClient initializes a new Redis client.
func NewRedisClient(addr string, password string, db int) (*RedisClient, error) {
	client := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: password,
		DB:       db,
	})

	// Verify connection.
	if err := client.Ping(context.Background()).Err(); err != nil {
		return nil, fmt.Errorf("db: ping redis: %w", err)
	}

	return &RedisClient{
		client: client,
	}, nil
}

// Client returns the underlying redis client.
func (r *RedisClient) Client() *redis.Client {
	return r.client
}

// Close closes the redis connection.
func (r *RedisClient) Close() error {
	return r.client.Close()
}

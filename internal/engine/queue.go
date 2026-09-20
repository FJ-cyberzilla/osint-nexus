package engine

import (
	"context"
)

// Task represents a unit of work to be performed.
type Task[T any] func(ctx context.Context) (T, error)

// Queue implements a generic, high-performance task queue using channels for concurrency.
type Queue[T any] struct {
	tasks chan Task[T]
}

// NewQueue initializes a new queue with the specified capacity.
func NewQueue[T any](capacity int) *Queue[T] {
	return &Queue[T]{
		tasks: make(chan Task[T], capacity),
	}
}

// Enqueue adds a task to the queue. This method blocks if the queue is full.
func (q *Queue[T]) Enqueue(ctx context.Context, task Task[T]) error {
	select {
	case q.tasks <- task:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// Dequeue retrieves a task from the queue. It blocks until a task is available
// or the context is cancelled.
func (q *Queue[T]) Dequeue(ctx context.Context) (Task[T], bool) {
	select {
	case task := <-q.tasks:
		return task, true
	case <-ctx.Done():
		return nil, false
	}
}

// Package complex demonstrates advanced Go patterns including concurrency.
package complex

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// Repository defines the interface for data access.
type Repository interface {
	Find(id int) (interface{}, error)
	FindAll() ([]interface{}, error)
	Save(entity interface{}) error
	Delete(id int) error
}

// InMemoryRepository implements Repository using a map.
type InMemoryRepository struct {
	mu    sync.RWMutex
	items map[int]interface{}
}

// NewInMemoryRepository creates a new in-memory repository.
func NewInMemoryRepository() *InMemoryRepository {
	return &InMemoryRepository{
		items: make(map[int]interface{}),
	}
}

// Find retrieves an item by ID.
func (r *InMemoryRepository) Find(id int) (interface{}, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if item, ok := r.items[id]; ok {
		return item, nil
	}
	return nil, errors.New("not found")
}

// FindAll retrieves all items.
func (r *InMemoryRepository) FindAll() ([]interface{}, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]interface{}, 0, len(r.items))
	for _, item := range r.items {
		result = append(result, item)
	}
	return result, nil
}

// Save stores an item with the given ID.
func (r *InMemoryRepository) Save(entity interface{}) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Simplified: use a hash or extract ID from entity in real implementation
	r.items[len(r.items)+1] = entity
	return nil
}

// Delete removes an item by ID.
func (r *InMemoryRepository) Delete(id int) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if _, ok := r.items[id]; !ok {
		return errors.New("not found")
	}
	delete(r.items, id)
	return nil
}

// Worker represents a concurrent worker.
type Worker struct {
	ID       int
	JobChan  chan Job
	Quit     chan bool
	wg       *sync.WaitGroup
}

// Job represents a unit of work.
type Job struct {
	ID      int
	Payload interface{}
}

// Result represents the result of a job.
type Result struct {
	JobID   int
	Success bool
	Error   error
}

// WorkerPool manages a pool of workers.
type WorkerPool struct {
	workers    []*Worker
	jobQueue   chan Job
	resultChan chan Result
	wg         sync.WaitGroup
}

// NewWorkerPool creates a new worker pool with the specified size.
func NewWorkerPool(size int) *WorkerPool {
	pool := &WorkerPool{
		workers:    make([]*Worker, size),
		jobQueue:   make(chan Job, 100),
		resultChan: make(chan Result, 100),
	}

	for i := 0; i < size; i++ {
		pool.workers[i] = &Worker{
			ID:      i,
			JobChan: pool.jobQueue,
			Quit:    make(chan bool),
			wg:      &pool.wg,
		}
		go pool.workers[i].Start(pool.resultChan)
	}

	return pool
}

// Start begins the worker's job processing loop.
func (w *Worker) Start(results chan<- Result) {
	for {
		select {
		case job := <-w.JobChan:
			// Process the job
			result := Result{
				JobID:   job.ID,
				Success: true,
			}
			// Simulate work
			time.Sleep(10 * time.Millisecond)
			results <- result
		case <-w.Quit:
			return
		}
	}
}

// Submit adds a job to the pool.
func (p *WorkerPool) Submit(job Job) {
	p.wg.Add(1)
	go func() {
		defer p.wg.Done()
		p.jobQueue <- job
	}()
}

// Shutdown gracefully stops all workers.
func (p *WorkerPool) Shutdown() {
	for _, worker := range p.workers {
		worker.Quit <- true
	}
	close(p.jobQueue)
	close(p.resultChan)
}

// Pipeline represents a data processing pipeline.
type Pipeline struct {
	stages []func(context.Context, interface{}) (interface{}, error)
}

// NewPipeline creates a new pipeline.
func NewPipeline() *Pipeline {
	return &Pipeline{
		stages: make([]func(context.Context, interface{}) (interface{}, error), 0),
	}
}

// AddStage adds a processing stage to the pipeline.
func (p *Pipeline) AddStage(stage func(context.Context, interface{}) (interface{}, error)) {
	p.stages = append(p.stages, stage)
}

// Execute runs the pipeline with the given input.
func (p *Pipeline) Execute(ctx context.Context, input interface{}) (interface{}, error) {
	result := input
	var err error

	for i, stage := range p.stages {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		default:
			result, err = stage(ctx, result)
			if err != nil {
				return nil, fmt.Errorf("stage %d failed: %w", i, err)
			}
		}
	}

	return result, nil
}

// RateLimiter implements a token bucket rate limiter.
type RateLimiter struct {
	tokens     chan struct{}
	interval   time.Duration
	maxTokens  int
	refillStop chan bool
}

// NewRateLimiter creates a new rate limiter.
func NewRateLimiter(rate int, interval time.Duration) *RateLimiter {
	rl := &RateLimiter{
		tokens:     make(chan struct{}, rate),
		interval:   interval,
		maxTokens:  rate,
		refillStop: make(chan bool),
	}

	// Fill initial tokens
	for i := 0; i < rate; i++ {
		rl.tokens <- struct{}{}
	}

	// Start refill goroutine
	go rl.refill()

	return rl
}

// refill periodically adds tokens to the bucket.
func (rl *RateLimiter) refill() {
	ticker := time.NewTicker(rl.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			select {
			case rl.tokens <- struct{}{}:
			default:
				// Bucket is full
			}
		case <-rl.refillStop:
			return
		}
	}
}

// Acquire blocks until a token is available.
func (rl *RateLimiter) Acquire(ctx context.Context) error {
	select {
	case <-rl.tokens:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// Stop stops the rate limiter.
func (rl *RateLimiter) Stop() {
	close(rl.refillStop)
}

// CircuitBreaker implements the circuit breaker pattern.
type CircuitBreaker struct {
	mu           sync.Mutex
	failures     int
	successes    int
	threshold    int
	resetTimeout time.Duration
	state        string
	lastFailure  time.Time
}

// NewCircuitBreaker creates a new circuit breaker.
func NewCircuitBreaker(threshold int, resetTimeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		threshold:    threshold,
		resetTimeout: resetTimeout,
		state:        "closed",
	}
}

// Execute runs the given function with circuit breaker protection.
func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()

	if cb.state == "open" {
		if time.Since(cb.lastFailure) > cb.resetTimeout {
			cb.state = "half-open"
		} else {
			cb.mu.Unlock()
			return errors.New("circuit breaker is open")
		}
	}
	cb.mu.Unlock()

	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failures++
		cb.lastFailure = time.Now()
		if cb.failures >= cb.threshold {
			cb.state = "open"
		}
		return err
	}

	if cb.state == "half-open" {
		cb.successes++
		if cb.successes >= cb.threshold {
			cb.state = "closed"
			cb.failures = 0
			cb.successes = 0
		}
	}

	return nil
}

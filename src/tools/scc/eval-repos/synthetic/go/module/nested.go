// Package module provides nested functionality.
package module

import (
	"sync"
)

// NestedItem represents an item in the nested service.
type NestedItem struct {
	ID        int
	Name      string
	CreatedAt int64
}

// NestedService provides item management.
type NestedService struct {
	items []NestedItem
	mu    sync.RWMutex
}

// NewNestedService creates a new service.
func NewNestedService() *NestedService {
	return &NestedService{
		items: make([]NestedItem, 0),
	}
}

// Add adds an item.
func (s *NestedService) Add(item NestedItem) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.items = append(s.items, item)
}

// Find searches for an item by ID.
func (s *NestedService) Find(id int) *NestedItem {
	s.mu.RLock()
	defer s.mu.RUnlock()

	for i := range s.items {
		if s.items[i].ID == id {
			return &s.items[i]
		}
	}
	return nil
}

// GetAll returns all items.
func (s *NestedService) GetAll() []NestedItem {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]NestedItem, len(s.items))
	copy(result, s.items)
	return result
}

// Clear removes all items.
func (s *NestedService) Clear() int {
	s.mu.Lock()
	defer s.mu.Unlock()

	count := len(s.items)
	s.items = s.items[:0]
	return count
}

// NestedProcessor processes items.
type NestedProcessor interface {
	Process(item NestedItem) (bool, error)
}

// AsyncProcessor implements NestedProcessor.
type AsyncProcessor struct{}

// Process processes an item asynchronously.
func (p *AsyncProcessor) Process(item NestedItem) (bool, error) {
	return item.ID > 0, nil
}

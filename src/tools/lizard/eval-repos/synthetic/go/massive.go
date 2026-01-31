// Package synthetic provides massive complexity Go code for testing.
// High complexity (CCN ~30+), 500+ LOC.
package synthetic

import (
	"container/heap"
	"errors"
	"sync"
)

// ===== BINARY SEARCH TREE =====

// TreeNode represents a node in a binary search tree.
type TreeNode struct {
	Value int
	Left  *TreeNode
	Right *TreeNode
}

// BST implements a binary search tree.
type BST struct {
	Root *TreeNode
	mu   sync.RWMutex
}

// Insert adds a value to the BST.
func (t *BST) Insert(value int) {
	t.mu.Lock()
	defer t.mu.Unlock()

	newNode := &TreeNode{Value: value}

	if t.Root == nil {
		t.Root = newNode
		return
	}

	current := t.Root
	for {
		if value < current.Value {
			if current.Left == nil {
				current.Left = newNode
				return
			}
			current = current.Left
		} else if value > current.Value {
			if current.Right == nil {
				current.Right = newNode
				return
			}
			current = current.Right
		} else {
			return // Duplicate
		}
	}
}

// Find searches for a value in the BST.
func (t *BST) Find(value int) bool {
	t.mu.RLock()
	defer t.mu.RUnlock()

	current := t.Root
	for current != nil {
		if value == current.Value {
			return true
		} else if value < current.Value {
			current = current.Left
		} else {
			current = current.Right
		}
	}
	return false
}

// Delete removes a value from the BST.
func (t *BST) Delete(value int) bool {
	t.mu.Lock()
	defer t.mu.Unlock()

	var parent *TreeNode
	current := t.Root
	isLeft := false

	for current != nil {
		if value == current.Value {
			break
		}
		parent = current
		if value < current.Value {
			current = current.Left
			isLeft = true
		} else {
			current = current.Right
			isLeft = false
		}
	}

	if current == nil {
		return false
	}

	// Leaf node
	if current.Left == nil && current.Right == nil {
		if current == t.Root {
			t.Root = nil
		} else if isLeft {
			parent.Left = nil
		} else {
			parent.Right = nil
		}
	} else if current.Right == nil {
		// One child (left)
		if current == t.Root {
			t.Root = current.Left
		} else if isLeft {
			parent.Left = current.Left
		} else {
			parent.Right = current.Left
		}
	} else if current.Left == nil {
		// One child (right)
		if current == t.Root {
			t.Root = current.Right
		} else if isLeft {
			parent.Left = current.Right
		} else {
			parent.Right = current.Right
		}
	} else {
		// Two children
		successor := t.findMin(current.Right)
		current.Value = successor
		t.deleteMin(current, current.Right)
	}

	return true
}

func (t *BST) findMin(node *TreeNode) int {
	for node.Left != nil {
		node = node.Left
	}
	return node.Value
}

func (t *BST) deleteMin(parent, node *TreeNode) {
	for node.Left != nil {
		parent = node
		node = node.Left
	}
	if parent.Left == node {
		parent.Left = node.Right
	} else {
		parent.Right = node.Right
	}
}

// InOrder returns values in sorted order.
func (t *BST) InOrder() []int {
	t.mu.RLock()
	defer t.mu.RUnlock()

	var result []int
	t.inOrderHelper(t.Root, &result)
	return result
}

func (t *BST) inOrderHelper(node *TreeNode, result *[]int) {
	if node != nil {
		t.inOrderHelper(node.Left, result)
		*result = append(*result, node.Value)
		t.inOrderHelper(node.Right, result)
	}
}

// ===== PRIORITY QUEUE =====

// PQItem represents an item in the priority queue.
type PQItem struct {
	Value    interface{}
	Priority int
	Index    int
}

// PriorityQueue implements heap.Interface.
type PriorityQueue []*PQItem

func (pq PriorityQueue) Len() int { return len(pq) }

func (pq PriorityQueue) Less(i, j int) bool {
	return pq[i].Priority < pq[j].Priority
}

func (pq PriorityQueue) Swap(i, j int) {
	pq[i], pq[j] = pq[j], pq[i]
	pq[i].Index = i
	pq[j].Index = j
}

func (pq *PriorityQueue) Push(x interface{}) {
	n := len(*pq)
	item := x.(*PQItem)
	item.Index = n
	*pq = append(*pq, item)
}

func (pq *PriorityQueue) Pop() interface{} {
	old := *pq
	n := len(old)
	item := old[n-1]
	old[n-1] = nil
	item.Index = -1
	*pq = old[0 : n-1]
	return item
}

// ===== GRAPH WITH DIJKSTRA =====

// Edge represents a weighted edge.
type Edge struct {
	To     int
	Weight int
}

// Graph represents a weighted directed graph.
type Graph struct {
	Vertices int
	Edges    map[int][]Edge
	mu       sync.RWMutex
}

// NewGraph creates a new graph.
func NewGraph(vertices int) *Graph {
	return &Graph{
		Vertices: vertices,
		Edges:    make(map[int][]Edge),
	}
}

// AddEdge adds a directed edge.
func (g *Graph) AddEdge(from, to, weight int) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.Edges[from] = append(g.Edges[from], Edge{To: to, Weight: weight})
}

// Dijkstra finds shortest paths from source.
func (g *Graph) Dijkstra(source int) []int {
	g.mu.RLock()
	defer g.mu.RUnlock()

	dist := make([]int, g.Vertices)
	for i := range dist {
		dist[i] = 1<<31 - 1 // MaxInt
	}
	dist[source] = 0

	pq := make(PriorityQueue, 0)
	heap.Init(&pq)
	heap.Push(&pq, &PQItem{Value: source, Priority: 0})

	visited := make([]bool, g.Vertices)

	for pq.Len() > 0 {
		item := heap.Pop(&pq).(*PQItem)
		u := item.Value.(int)

		if visited[u] {
			continue
		}
		visited[u] = true

		for _, edge := range g.Edges[u] {
			if visited[edge.To] {
				continue
			}
			newDist := dist[u] + edge.Weight
			if newDist < dist[edge.To] {
				dist[edge.To] = newDist
				heap.Push(&pq, &PQItem{Value: edge.To, Priority: newDist})
			}
		}
	}

	return dist
}

// BFS performs breadth-first search.
func (g *Graph) BFS(start int) []int {
	g.mu.RLock()
	defer g.mu.RUnlock()

	visited := make([]bool, g.Vertices)
	queue := []int{start}
	var result []int

	for len(queue) > 0 {
		u := queue[0]
		queue = queue[1:]

		if visited[u] {
			continue
		}
		visited[u] = true
		result = append(result, u)

		for _, edge := range g.Edges[u] {
			if !visited[edge.To] {
				queue = append(queue, edge.To)
			}
		}
	}

	return result
}

// DFS performs depth-first search.
func (g *Graph) DFS(start int) []int {
	g.mu.RLock()
	defer g.mu.RUnlock()

	visited := make([]bool, g.Vertices)
	var result []int
	g.dfsHelper(start, visited, &result)
	return result
}

func (g *Graph) dfsHelper(u int, visited []bool, result *[]int) {
	if visited[u] {
		return
	}
	visited[u] = true
	*result = append(*result, u)

	for _, edge := range g.Edges[u] {
		g.dfsHelper(edge.To, visited, result)
	}
}

// ===== SORTING =====

// QuickSort sorts a slice in place.
func QuickSort(arr []int) {
	if len(arr) <= 1 {
		return
	}
	quickSortHelper(arr, 0, len(arr)-1)
}

func quickSortHelper(arr []int, low, high int) {
	if low < high {
		p := partition(arr, low, high)
		quickSortHelper(arr, low, p-1)
		quickSortHelper(arr, p+1, high)
	}
}

func partition(arr []int, low, high int) int {
	pivot := arr[high]
	i := low - 1

	for j := low; j < high; j++ {
		if arr[j] < pivot {
			i++
			arr[i], arr[j] = arr[j], arr[i]
		}
	}
	arr[i+1], arr[high] = arr[high], arr[i+1]
	return i + 1
}

// MergeSort returns a sorted copy.
func MergeSort(arr []int) []int {
	if len(arr) <= 1 {
		return arr
	}

	mid := len(arr) / 2
	left := MergeSort(arr[:mid])
	right := MergeSort(arr[mid:])

	return merge(left, right)
}

func merge(left, right []int) []int {
	result := make([]int, 0, len(left)+len(right))
	i, j := 0, 0

	for i < len(left) && j < len(right) {
		if left[i] <= right[j] {
			result = append(result, left[i])
			i++
		} else {
			result = append(result, right[j])
			j++
		}
	}

	result = append(result, left[i:]...)
	result = append(result, right[j:]...)
	return result
}

// ===== DYNAMIC PROGRAMMING =====

// LCS finds the longest common subsequence.
func LCS(s1, s2 string) string {
	m, n := len(s1), len(s2)
	dp := make([][]int, m+1)
	for i := range dp {
		dp[i] = make([]int, n+1)
	}

	for i := 1; i <= m; i++ {
		for j := 1; j <= n; j++ {
			if s1[i-1] == s2[j-1] {
				dp[i][j] = dp[i-1][j-1] + 1
			} else {
				if dp[i-1][j] > dp[i][j-1] {
					dp[i][j] = dp[i-1][j]
				} else {
					dp[i][j] = dp[i][j-1]
				}
			}
		}
	}

	// Backtrack
	lcs := make([]byte, 0, dp[m][n])
	i, j := m, n
	for i > 0 && j > 0 {
		if s1[i-1] == s2[j-1] {
			lcs = append([]byte{s1[i-1]}, lcs...)
			i--
			j--
		} else if dp[i-1][j] > dp[i][j-1] {
			i--
		} else {
			j--
		}
	}

	return string(lcs)
}

// EditDistance computes Levenshtein distance.
func EditDistance(s1, s2 string) int {
	m, n := len(s1), len(s2)
	dp := make([][]int, m+1)
	for i := range dp {
		dp[i] = make([]int, n+1)
	}

	for i := 0; i <= m; i++ {
		dp[i][0] = i
	}
	for j := 0; j <= n; j++ {
		dp[0][j] = j
	}

	for i := 1; i <= m; i++ {
		for j := 1; j <= n; j++ {
			if s1[i-1] == s2[j-1] {
				dp[i][j] = dp[i-1][j-1]
			} else {
				min := dp[i-1][j]
				if dp[i][j-1] < min {
					min = dp[i][j-1]
				}
				if dp[i-1][j-1] < min {
					min = dp[i-1][j-1]
				}
				dp[i][j] = 1 + min
			}
		}
	}

	return dp[m][n]
}

// Knapsack solves the 0/1 knapsack problem.
func Knapsack(weights, values []int, capacity int) int {
	n := len(weights)
	dp := make([][]int, n+1)
	for i := range dp {
		dp[i] = make([]int, capacity+1)
	}

	for i := 1; i <= n; i++ {
		for w := 0; w <= capacity; w++ {
			if weights[i-1] <= w {
				include := dp[i-1][w-weights[i-1]] + values[i-1]
				exclude := dp[i-1][w]
				if include > exclude {
					dp[i][w] = include
				} else {
					dp[i][w] = exclude
				}
			} else {
				dp[i][w] = dp[i-1][w]
			}
		}
	}

	return dp[n][capacity]
}

// ErrNotFound is returned when an item is not found.
var ErrNotFound = errors.New("item not found")

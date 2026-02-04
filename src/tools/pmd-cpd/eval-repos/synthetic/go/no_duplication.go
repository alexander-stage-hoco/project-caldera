// Package synthetic contains Go files for CPD testing with no code duplication.
package synthetic

import (
	"math"
	"sort"
)

// CalculateFibonacci calculates the nth Fibonacci number.
func CalculateFibonacci(n int) int64 {
	if n <= 1 {
		return int64(n)
	}
	var a, b int64 = 0, 1
	for i := 2; i <= n; i++ {
		a, b = b, a+b
	}
	return b
}

// IsPrime checks if a number is prime.
func IsPrime(num int) bool {
	if num < 2 {
		return false
	}
	if num == 2 {
		return true
	}
	if num%2 == 0 {
		return false
	}
	for i := 3; i <= int(math.Sqrt(float64(num))); i += 2 {
		if num%i == 0 {
			return false
		}
	}
	return true
}

// BinarySearch performs binary search on a sorted array.
func BinarySearch(arr []int, target int) int {
	left, right := 0, len(arr)-1
	for left <= right {
		mid := (left + right) / 2
		if arr[mid] == target {
			return mid
		}
		if arr[mid] < target {
			left = mid + 1
		} else {
			right = mid - 1
		}
	}
	return -1
}

// DataProcessor processes numerical data.
type DataProcessor struct {
	data      []float64
	processed bool
}

// NewDataProcessor creates a new DataProcessor.
func NewDataProcessor(data []float64) *DataProcessor {
	return &DataProcessor{data: data}
}

// Normalize normalizes the data to 0-1 range.
func (dp *DataProcessor) Normalize() []float64 {
	if len(dp.data) == 0 {
		return []float64{}
	}
	min, max := dp.data[0], dp.data[0]
	for _, v := range dp.data {
		if v < min {
			min = v
		}
		if v > max {
			max = v
		}
	}
	if max == min {
		result := make([]float64, len(dp.data))
		for i := range result {
			result[i] = 0.5
		}
		return result
	}
	result := make([]float64, len(dp.data))
	for i, v := range dp.data {
		result[i] = (v - min) / (max - min)
	}
	return result
}

// Statistics contains computed statistics.
type Statistics struct {
	Mean   float64
	Median float64
	Std    float64
}

// ComputeStatistics computes basic statistics on the data.
func (dp *DataProcessor) ComputeStatistics() Statistics {
	if len(dp.data) == 0 {
		return Statistics{}
	}
	n := float64(len(dp.data))
	var sum float64
	for _, v := range dp.data {
		sum += v
	}
	mean := sum / n

	sorted := make([]float64, len(dp.data))
	copy(sorted, dp.data)
	sort.Float64s(sorted)
	var median float64
	if len(sorted)%2 != 0 {
		median = sorted[len(sorted)/2]
	} else {
		median = (sorted[len(sorted)/2-1] + sorted[len(sorted)/2]) / 2
	}

	var varianceSum float64
	for _, v := range dp.data {
		varianceSum += (v - mean) * (v - mean)
	}
	std := math.Sqrt(varianceSum / n)

	return Statistics{Mean: mean, Median: median, Std: std}
}

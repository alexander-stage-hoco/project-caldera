/**
 * JavaScript file with no code duplication - all functions are unique.
 */

function calculateFibonacci(n) {
    if (n <= 1) return n;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) {
        [a, b] = [b, a + b];
    }
    return b;
}

function isPrime(num) {
    if (num < 2) return false;
    if (num === 2) return true;
    if (num % 2 === 0) return false;
    for (let i = 3; i <= Math.sqrt(num); i += 2) {
        if (num % i === 0) return false;
    }
    return true;
}

function binarySearch(arr, target) {
    let left = 0, right = arr.length - 1;
    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        if (arr[mid] === target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

function mergeSort(arr) {
    if (arr.length <= 1) return arr;
    const mid = Math.floor(arr.length / 2);
    const left = mergeSort(arr.slice(0, mid));
    const right = mergeSort(arr.slice(mid));
    return merge(left, right);
}

function merge(left, right) {
    const result = [];
    let i = 0, j = 0;
    while (i < left.length && j < right.length) {
        if (left[i] <= right[j]) {
            result.push(left[i++]);
        } else {
            result.push(right[j++]);
        }
    }
    return result.concat(left.slice(i)).concat(right.slice(j));
}

class DataProcessor {
    constructor(data) {
        this.data = data;
        this.processed = false;
    }

    normalize() {
        if (!this.data.length) return [];
        const min = Math.min(...this.data);
        const max = Math.max(...this.data);
        if (max === min) return this.data.map(() => 0.5);
        return this.data.map(x => (x - min) / (max - min));
    }

    computeStatistics() {
        if (!this.data.length) return { mean: 0, median: 0, std: 0 };
        const n = this.data.length;
        const mean = this.data.reduce((a, b) => a + b, 0) / n;
        const sorted = [...this.data].sort((a, b) => a - b);
        const median = n % 2 ? sorted[Math.floor(n / 2)] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2;
        const variance = this.data.reduce((sum, x) => sum + (x - mean) ** 2, 0) / n;
        return { mean, median, std: Math.sqrt(variance) };
    }
}

module.exports = { calculateFibonacci, isPrime, binarySearch, mergeSort, DataProcessor };

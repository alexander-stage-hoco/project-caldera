//! Rust file with no code duplication - all functions are unique.

/// Calculate the nth Fibonacci number.
pub fn calculate_fibonacci(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    let (mut a, mut b) = (0u64, 1u64);
    for _ in 2..=n {
        let temp = a + b;
        a = b;
        b = temp;
    }
    b
}

/// Check if a number is prime.
pub fn is_prime(num: u64) -> bool {
    if num < 2 {
        return false;
    }
    if num == 2 {
        return true;
    }
    if num % 2 == 0 {
        return false;
    }
    let sqrt = (num as f64).sqrt() as u64;
    for i in (3..=sqrt).step_by(2) {
        if num % i == 0 {
            return false;
        }
    }
    true
}

/// Perform binary search on a sorted array.
pub fn binary_search(arr: &[i32], target: i32) -> Option<usize> {
    let (mut left, mut right) = (0, arr.len());
    while left < right {
        let mid = (left + right) / 2;
        if arr[mid] == target {
            return Some(mid);
        }
        if arr[mid] < target {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    None
}

/// Data processor for numerical data.
pub struct DataProcessor {
    data: Vec<f64>,
    processed: bool,
}

impl DataProcessor {
    pub fn new(data: Vec<f64>) -> Self {
        Self { data, processed: false }
    }

    /// Normalize the data to 0-1 range.
    pub fn normalize(&self) -> Vec<f64> {
        if self.data.is_empty() {
            return vec![];
        }
        let min = self.data.iter().cloned().fold(f64::INFINITY, f64::min);
        let max = self.data.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        if (max - min).abs() < f64::EPSILON {
            return vec![0.5; self.data.len()];
        }
        self.data.iter().map(|x| (x - min) / (max - min)).collect()
    }

    /// Compute basic statistics on the data.
    pub fn compute_statistics(&self) -> Statistics {
        if self.data.is_empty() {
            return Statistics::default();
        }
        let n = self.data.len() as f64;
        let mean = self.data.iter().sum::<f64>() / n;

        let mut sorted = self.data.clone();
        sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let median = if sorted.len() % 2 != 0 {
            sorted[sorted.len() / 2]
        } else {
            (sorted[sorted.len() / 2 - 1] + sorted[sorted.len() / 2]) / 2.0
        };

        let variance = self.data.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / n;
        Statistics { mean, median, std: variance.sqrt() }
    }
}

#[derive(Default, Debug)]
pub struct Statistics {
    pub mean: f64,
    pub median: f64,
    pub std: f64,
}

//! Massive Rust file - High complexity (CCN ~30+), 500+ LOC
//! Contains advanced Rust patterns with complex logic.

use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap, HashSet, VecDeque};

// ===== BINARY SEARCH TREE =====

#[derive(Debug)]
struct TreeNode<T> {
    value: T,
    left: Option<Box<TreeNode<T>>>,
    right: Option<Box<TreeNode<T>>>,
}

#[derive(Debug, Default)]
pub struct BST<T: Ord> {
    root: Option<Box<TreeNode<T>>>,
}

impl<T: Ord + Clone> BST<T> {
    pub fn new() -> Self {
        BST { root: None }
    }

    pub fn insert(&mut self, value: T) {
        let new_node = Box::new(TreeNode {
            value,
            left: None,
            right: None,
        });

        match &mut self.root {
            None => self.root = Some(new_node),
            Some(root) => Self::insert_recursive(root, new_node),
        }
    }

    fn insert_recursive(current: &mut Box<TreeNode<T>>, new_node: Box<TreeNode<T>>) {
        match new_node.value.cmp(&current.value) {
            Ordering::Less => match &mut current.left {
                None => current.left = Some(new_node),
                Some(left) => Self::insert_recursive(left, new_node),
            },
            Ordering::Greater => match &mut current.right {
                None => current.right = Some(new_node),
                Some(right) => Self::insert_recursive(right, new_node),
            },
            Ordering::Equal => {}
        }
    }

    pub fn find(&self, value: &T) -> bool {
        Self::find_recursive(&self.root, value)
    }

    fn find_recursive(node: &Option<Box<TreeNode<T>>>, value: &T) -> bool {
        match node {
            None => false,
            Some(n) => match value.cmp(&n.value) {
                Ordering::Equal => true,
                Ordering::Less => Self::find_recursive(&n.left, value),
                Ordering::Greater => Self::find_recursive(&n.right, value),
            },
        }
    }

    pub fn in_order(&self) -> Vec<T> {
        let mut result = Vec::new();
        Self::in_order_recursive(&self.root, &mut result);
        result
    }

    fn in_order_recursive(node: &Option<Box<TreeNode<T>>>, result: &mut Vec<T>) {
        if let Some(n) = node {
            Self::in_order_recursive(&n.left, result);
            result.push(n.value.clone());
            Self::in_order_recursive(&n.right, result);
        }
    }
}

// ===== PRIORITY QUEUE ITEM =====

#[derive(Debug, Clone, Eq, PartialEq)]
struct PQItem<T> {
    value: T,
    priority: i32,
}

impl<T: Eq> Ord for PQItem<T> {
    fn cmp(&self, other: &Self) -> Ordering {
        other.priority.cmp(&self.priority) // Min-heap
    }
}

impl<T: Eq> PartialOrd for PQItem<T> {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

// ===== GRAPH WITH DIJKSTRA =====

#[derive(Debug, Clone)]
pub struct Edge {
    to: usize,
    weight: i32,
}

#[derive(Debug)]
pub struct Graph {
    vertices: usize,
    edges: HashMap<usize, Vec<Edge>>,
}

impl Graph {
    pub fn new(vertices: usize) -> Self {
        Graph {
            vertices,
            edges: HashMap::new(),
        }
    }

    pub fn add_edge(&mut self, from: usize, to: usize, weight: i32) {
        self.edges
            .entry(from)
            .or_insert_with(Vec::new)
            .push(Edge { to, weight });
    }

    pub fn dijkstra(&self, source: usize) -> Vec<i32> {
        let mut dist = vec![i32::MAX; self.vertices];
        let mut visited = vec![false; self.vertices];
        let mut heap = BinaryHeap::new();

        dist[source] = 0;
        heap.push(PQItem {
            value: source,
            priority: 0,
        });

        while let Some(PQItem { value: u, .. }) = heap.pop() {
            if visited[u] {
                continue;
            }
            visited[u] = true;

            if let Some(edges) = self.edges.get(&u) {
                for edge in edges {
                    if visited[edge.to] {
                        continue;
                    }
                    let new_dist = dist[u].saturating_add(edge.weight);
                    if new_dist < dist[edge.to] {
                        dist[edge.to] = new_dist;
                        heap.push(PQItem {
                            value: edge.to,
                            priority: new_dist,
                        });
                    }
                }
            }
        }

        dist
    }

    pub fn bfs(&self, start: usize) -> Vec<usize> {
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        let mut result = Vec::new();

        queue.push_back(start);

        while let Some(u) = queue.pop_front() {
            if visited.contains(&u) {
                continue;
            }
            visited.insert(u);
            result.push(u);

            if let Some(edges) = self.edges.get(&u) {
                for edge in edges {
                    if !visited.contains(&edge.to) {
                        queue.push_back(edge.to);
                    }
                }
            }
        }

        result
    }

    pub fn dfs(&self, start: usize) -> Vec<usize> {
        let mut visited = HashSet::new();
        let mut result = Vec::new();
        self.dfs_helper(start, &mut visited, &mut result);
        result
    }

    fn dfs_helper(&self, u: usize, visited: &mut HashSet<usize>, result: &mut Vec<usize>) {
        if visited.contains(&u) {
            return;
        }
        visited.insert(u);
        result.push(u);

        if let Some(edges) = self.edges.get(&u) {
            for edge in edges {
                self.dfs_helper(edge.to, visited, result);
            }
        }
    }
}

// ===== SORTING =====

pub fn quick_sort<T: Ord + Clone>(arr: &mut [T]) {
    if arr.len() <= 1 {
        return;
    }
    let len = arr.len();
    quick_sort_helper(arr, 0, len - 1);
}

fn quick_sort_helper<T: Ord + Clone>(arr: &mut [T], low: usize, high: usize) {
    if low < high {
        let p = partition(arr, low, high);
        if p > 0 {
            quick_sort_helper(arr, low, p - 1);
        }
        quick_sort_helper(arr, p + 1, high);
    }
}

fn partition<T: Ord + Clone>(arr: &mut [T], low: usize, high: usize) -> usize {
    let pivot = arr[high].clone();
    let mut i = low;

    for j in low..high {
        if arr[j] < pivot {
            arr.swap(i, j);
            i += 1;
        }
    }
    arr.swap(i, high);
    i
}

pub fn merge_sort<T: Ord + Clone>(arr: &[T]) -> Vec<T> {
    if arr.len() <= 1 {
        return arr.to_vec();
    }

    let mid = arr.len() / 2;
    let left = merge_sort(&arr[..mid]);
    let right = merge_sort(&arr[mid..]);

    merge(&left, &right)
}

fn merge<T: Ord + Clone>(left: &[T], right: &[T]) -> Vec<T> {
    let mut result = Vec::with_capacity(left.len() + right.len());
    let (mut i, mut j) = (0, 0);

    while i < left.len() && j < right.len() {
        if left[i] <= right[j] {
            result.push(left[i].clone());
            i += 1;
        } else {
            result.push(right[j].clone());
            j += 1;
        }
    }

    result.extend_from_slice(&left[i..]);
    result.extend_from_slice(&right[j..]);
    result
}

// ===== DYNAMIC PROGRAMMING =====

pub fn lcs(s1: &str, s2: &str) -> String {
    let (m, n) = (s1.len(), s2.len());
    let s1: Vec<char> = s1.chars().collect();
    let s2: Vec<char> = s2.chars().collect();

    let mut dp = vec![vec![0; n + 1]; m + 1];

    for i in 1..=m {
        for j in 1..=n {
            if s1[i - 1] == s2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = dp[i - 1][j].max(dp[i][j - 1]);
            }
        }
    }

    // Backtrack
    let mut result = String::new();
    let (mut i, mut j) = (m, n);

    while i > 0 && j > 0 {
        if s1[i - 1] == s2[j - 1] {
            result.insert(0, s1[i - 1]);
            i -= 1;
            j -= 1;
        } else if dp[i - 1][j] > dp[i][j - 1] {
            i -= 1;
        } else {
            j -= 1;
        }
    }

    result
}

pub fn edit_distance(s1: &str, s2: &str) -> usize {
    let (m, n) = (s1.len(), s2.len());
    let s1: Vec<char> = s1.chars().collect();
    let s2: Vec<char> = s2.chars().collect();

    let mut dp = vec![vec![0; n + 1]; m + 1];

    for i in 0..=m {
        dp[i][0] = i;
    }
    for j in 0..=n {
        dp[0][j] = j;
    }

    for i in 1..=m {
        for j in 1..=n {
            if s1[i - 1] == s2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + dp[i - 1][j].min(dp[i][j - 1]).min(dp[i - 1][j - 1]);
            }
        }
    }

    dp[m][n]
}

pub fn knapsack(weights: &[usize], values: &[i32], capacity: usize) -> i32 {
    let n = weights.len();
    let mut dp = vec![vec![0; capacity + 1]; n + 1];

    for i in 1..=n {
        for w in 0..=capacity {
            if weights[i - 1] <= w {
                dp[i][w] = dp[i - 1][w].max(dp[i - 1][w - weights[i - 1]] + values[i - 1]);
            } else {
                dp[i][w] = dp[i - 1][w];
            }
        }
    }

    dp[n][capacity]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bst() {
        let mut tree = BST::new();
        tree.insert(5);
        tree.insert(3);
        tree.insert(7);
        assert!(tree.find(&5));
        assert!(!tree.find(&10));
    }

    #[test]
    fn test_quick_sort() {
        let mut arr = vec![3, 1, 4, 1, 5, 9, 2, 6];
        quick_sort(&mut arr);
        assert_eq!(arr, vec![1, 1, 2, 3, 4, 5, 6, 9]);
    }
}

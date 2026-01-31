/**
 * Massive TypeScript file - High complexity (CCN ~30+), 500+ LOC
 * Contains advanced TypeScript patterns with complex logic.
 */

// ===== TYPE DEFINITIONS =====

interface TreeNode<T> {
  value: T;
  left: TreeNode<T> | null;
  right: TreeNode<T> | null;
}

interface GraphEdge<T> {
  from: T;
  to: T;
  weight: number;
}

type Comparator<T> = (a: T, b: T) => number;

interface PriorityQueueItem<T> {
  value: T;
  priority: number;
}

// ===== BINARY SEARCH TREE =====

class BinarySearchTree<T> {
  private root: TreeNode<T> | null = null;
  private comparator: Comparator<T>;

  constructor(comparator: Comparator<T>) {
    this.comparator = comparator;
  }

  insert(value: T): void {
    const newNode: TreeNode<T> = { value, left: null, right: null };

    if (this.root === null) {
      this.root = newNode;
      return;
    }

    let current = this.root;
    while (true) {
      const comparison = this.comparator(value, current.value);

      if (comparison < 0) {
        if (current.left === null) {
          current.left = newNode;
          return;
        }
        current = current.left;
      } else if (comparison > 0) {
        if (current.right === null) {
          current.right = newNode;
          return;
        }
        current = current.right;
      } else {
        return; // Duplicate, ignore
      }
    }
  }

  find(value: T): T | null {
    let current = this.root;

    while (current !== null) {
      const comparison = this.comparator(value, current.value);

      if (comparison === 0) {
        return current.value;
      } else if (comparison < 0) {
        current = current.left;
      } else {
        current = current.right;
      }
    }

    return null;
  }

  delete(value: T): boolean {
    let parent: TreeNode<T> | null = null;
    let current = this.root;
    let isLeftChild = false;

    while (current !== null) {
      const comparison = this.comparator(value, current.value);

      if (comparison === 0) {
        break;
      }

      parent = current;
      if (comparison < 0) {
        current = current.left;
        isLeftChild = true;
      } else {
        current = current.right;
        isLeftChild = false;
      }
    }

    if (current === null) {
      return false;
    }

    // Case 1: Leaf node
    if (current.left === null && current.right === null) {
      if (current === this.root) {
        this.root = null;
      } else if (isLeftChild) {
        parent!.left = null;
      } else {
        parent!.right = null;
      }
    }
    // Case 2: One child
    else if (current.right === null) {
      if (current === this.root) {
        this.root = current.left;
      } else if (isLeftChild) {
        parent!.left = current.left;
      } else {
        parent!.right = current.left;
      }
    } else if (current.left === null) {
      if (current === this.root) {
        this.root = current.right;
      } else if (isLeftChild) {
        parent!.left = current.right;
      } else {
        parent!.right = current.right;
      }
    }
    // Case 3: Two children
    else {
      const successor = this.findMin(current.right);
      current.value = successor;
      this.deleteMin(current, current.right);
    }

    return true;
  }

  private findMin(node: TreeNode<T>): T {
    while (node.left !== null) {
      node = node.left;
    }
    return node.value;
  }

  private deleteMin(parent: TreeNode<T>, node: TreeNode<T>): void {
    while (node.left !== null) {
      parent = node;
      node = node.left;
    }

    if (parent.left === node) {
      parent.left = node.right;
    } else {
      parent.right = node.right;
    }
  }

  inorderTraversal(): T[] {
    const result: T[] = [];
    this.inorderHelper(this.root, result);
    return result;
  }

  private inorderHelper(node: TreeNode<T> | null, result: T[]): void {
    if (node !== null) {
      this.inorderHelper(node.left, result);
      result.push(node.value);
      this.inorderHelper(node.right, result);
    }
  }
}

// ===== PRIORITY QUEUE =====

class PriorityQueue<T> {
  private heap: PriorityQueueItem<T>[] = [];

  enqueue(value: T, priority: number): void {
    this.heap.push({ value, priority });
    this.bubbleUp(this.heap.length - 1);
  }

  dequeue(): T | null {
    if (this.heap.length === 0) {
      return null;
    }

    const result = this.heap[0].value;

    if (this.heap.length === 1) {
      this.heap.pop();
    } else {
      this.heap[0] = this.heap.pop()!;
      this.bubbleDown(0);
    }

    return result;
  }

  private bubbleUp(index: number): void {
    while (index > 0) {
      const parentIndex = Math.floor((index - 1) / 2);

      if (this.heap[parentIndex].priority <= this.heap[index].priority) {
        break;
      }

      [this.heap[parentIndex], this.heap[index]] = [
        this.heap[index],
        this.heap[parentIndex],
      ];
      index = parentIndex;
    }
  }

  private bubbleDown(index: number): void {
    while (true) {
      const leftChild = 2 * index + 1;
      const rightChild = 2 * index + 2;
      let smallest = index;

      if (
        leftChild < this.heap.length &&
        this.heap[leftChild].priority < this.heap[smallest].priority
      ) {
        smallest = leftChild;
      }

      if (
        rightChild < this.heap.length &&
        this.heap[rightChild].priority < this.heap[smallest].priority
      ) {
        smallest = rightChild;
      }

      if (smallest === index) {
        break;
      }

      [this.heap[index], this.heap[smallest]] = [
        this.heap[smallest],
        this.heap[index],
      ];
      index = smallest;
    }
  }

  get size(): number {
    return this.heap.length;
  }
}

// ===== GRAPH WITH DIJKSTRA =====

class Graph<T> {
  private adjacencyList: Map<T, GraphEdge<T>[]> = new Map();

  addVertex(vertex: T): void {
    if (!this.adjacencyList.has(vertex)) {
      this.adjacencyList.set(vertex, []);
    }
  }

  addEdge(from: T, to: T, weight: number): void {
    this.addVertex(from);
    this.addVertex(to);
    this.adjacencyList.get(from)!.push({ from, to, weight });
  }

  dijkstra(start: T): Map<T, number> {
    const distances: Map<T, number> = new Map();
    const visited: Set<T> = new Set();
    const pq = new PriorityQueue<T>();

    for (const vertex of this.adjacencyList.keys()) {
      distances.set(vertex, Infinity);
    }
    distances.set(start, 0);
    pq.enqueue(start, 0);

    while (pq.size > 0) {
      const current = pq.dequeue()!;

      if (visited.has(current)) {
        continue;
      }
      visited.add(current);

      const edges = this.adjacencyList.get(current);
      if (edges) {
        for (const edge of edges) {
          if (visited.has(edge.to)) {
            continue;
          }

          const newDistance = distances.get(current)! + edge.weight;
          if (newDistance < distances.get(edge.to)!) {
            distances.set(edge.to, newDistance);
            pq.enqueue(edge.to, newDistance);
          }
        }
      }
    }

    return distances;
  }

  bfs(start: T): T[] {
    const visited: Set<T> = new Set();
    const queue: T[] = [start];
    const result: T[] = [];

    while (queue.length > 0) {
      const current = queue.shift()!;

      if (visited.has(current)) {
        continue;
      }

      visited.add(current);
      result.push(current);

      const edges = this.adjacencyList.get(current);
      if (edges) {
        for (const edge of edges) {
          if (!visited.has(edge.to)) {
            queue.push(edge.to);
          }
        }
      }
    }

    return result;
  }

  dfs(start: T): T[] {
    const visited: Set<T> = new Set();
    const result: T[] = [];
    this.dfsHelper(start, visited, result);
    return result;
  }

  private dfsHelper(vertex: T, visited: Set<T>, result: T[]): void {
    if (visited.has(vertex)) {
      return;
    }

    visited.add(vertex);
    result.push(vertex);

    const edges = this.adjacencyList.get(vertex);
    if (edges) {
      for (const edge of edges) {
        this.dfsHelper(edge.to, visited, result);
      }
    }
  }
}

// ===== SORTING ALGORITHMS =====

function quickSort<T>(arr: T[], comparator: Comparator<T>): T[] {
  if (arr.length <= 1) {
    return arr;
  }

  const pivot = arr[Math.floor(arr.length / 2)];
  const left: T[] = [];
  const middle: T[] = [];
  const right: T[] = [];

  for (const item of arr) {
    const cmp = comparator(item, pivot);
    if (cmp < 0) {
      left.push(item);
    } else if (cmp > 0) {
      right.push(item);
    } else {
      middle.push(item);
    }
  }

  return [...quickSort(left, comparator), ...middle, ...quickSort(right, comparator)];
}

function mergeSort<T>(arr: T[], comparator: Comparator<T>): T[] {
  if (arr.length <= 1) {
    return arr;
  }

  const mid = Math.floor(arr.length / 2);
  const left = mergeSort(arr.slice(0, mid), comparator);
  const right = mergeSort(arr.slice(mid), comparator);

  return merge(left, right, comparator);
}

function merge<T>(left: T[], right: T[], comparator: Comparator<T>): T[] {
  const result: T[] = [];
  let i = 0;
  let j = 0;

  while (i < left.length && j < right.length) {
    if (comparator(left[i], right[j]) <= 0) {
      result.push(left[i]);
      i++;
    } else {
      result.push(right[j]);
      j++;
    }
  }

  while (i < left.length) {
    result.push(left[i]);
    i++;
  }

  while (j < right.length) {
    result.push(right[j]);
    j++;
  }

  return result;
}

// ===== DYNAMIC PROGRAMMING =====

function longestCommonSubsequence(s1: string, s2: string): string {
  const m = s1.length;
  const n = s2.length;
  const dp: number[][] = Array(m + 1)
    .fill(null)
    .map(() => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (s1[i - 1] === s2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to find the LCS
  let lcs = '';
  let i = m;
  let j = n;

  while (i > 0 && j > 0) {
    if (s1[i - 1] === s2[j - 1]) {
      lcs = s1[i - 1] + lcs;
      i--;
      j--;
    } else if (dp[i - 1][j] > dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }

  return lcs;
}

function editDistance(s1: string, s2: string): number {
  const m = s1.length;
  const n = s2.length;
  const dp: number[][] = Array(m + 1)
    .fill(null)
    .map(() => Array(n + 1).fill(0));

  for (let i = 0; i <= m; i++) {
    dp[i][0] = i;
  }
  for (let j = 0; j <= n; j++) {
    dp[0][j] = j;
  }

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (s1[i - 1] === s2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
      }
    }
  }

  return dp[m][n];
}

function knapsack(weights: number[], values: number[], capacity: number): number {
  const n = weights.length;
  const dp: number[][] = Array(n + 1)
    .fill(null)
    .map(() => Array(capacity + 1).fill(0));

  for (let i = 1; i <= n; i++) {
    for (let w = 0; w <= capacity; w++) {
      if (weights[i - 1] <= w) {
        dp[i][w] = Math.max(
          dp[i - 1][w],
          dp[i - 1][w - weights[i - 1]] + values[i - 1]
        );
      } else {
        dp[i][w] = dp[i - 1][w];
      }
    }
  }

  return dp[n][capacity];
}

// ===== EXPORTS =====

export {
  BinarySearchTree,
  PriorityQueue,
  Graph,
  quickSort,
  mergeSort,
  longestCommonSubsequence,
  editDistance,
  knapsack,
  TreeNode,
  GraphEdge,
  Comparator,
};

/**
 * Massive JavaScript file with high complexity (500+ LOC, CCN 30+).
 * Contains complex algorithms and data structures.
 */

// =============================================================================
// Graph Implementation
// =============================================================================

class Graph {
    constructor() {
        this.adjacency = new Map();
        this.nodes = new Set();
    }

    addNode(node) {
        this.nodes.add(node);
        if (!this.adjacency.has(node)) {
            this.adjacency.set(node, []);
        }
    }

    addEdge(source, target, weight = 1) {
        this.addNode(source);
        this.addNode(target);
        this.adjacency.get(source).push({ target, weight });
    }

    dijkstra(start, end) {
        if (!this.nodes.has(start) || !this.nodes.has(end)) {
            return { distance: Infinity, path: [] };
        }

        const distances = new Map();
        const previous = new Map();
        const visited = new Set();

        for (const node of this.nodes) {
            distances.set(node, Infinity);
            previous.set(node, null);
        }
        distances.set(start, 0);

        const heap = [{ dist: 0, node: start }];

        while (heap.length > 0) {
            heap.sort((a, b) => a.dist - b.dist);
            const { dist: currentDist, node: current } = heap.shift();

            if (visited.has(current)) continue;

            if (current === end) {
                const path = [];
                let node = end;
                while (node !== null) {
                    path.unshift(node);
                    node = previous.get(node);
                }
                return { distance: currentDist, path };
            }

            visited.add(current);

            const neighbors = this.adjacency.get(current) || [];
            for (const { target: neighbor, weight } of neighbors) {
                if (visited.has(neighbor)) continue;

                const newDist = currentDist + weight;
                if (newDist < distances.get(neighbor)) {
                    distances.set(neighbor, newDist);
                    previous.set(neighbor, current);
                    heap.push({ dist: newDist, node: neighbor });
                }
            }
        }

        return { distance: Infinity, path: [] };
    }

    bfs(start) {
        if (!this.nodes.has(start)) return [];

        const visited = new Set();
        const queue = [start];
        const result = [];

        while (queue.length > 0) {
            const node = queue.shift();
            if (visited.has(node)) continue;

            visited.add(node);
            result.push(node);

            const neighbors = this.adjacency.get(node) || [];
            for (const { target: neighbor } of neighbors) {
                if (!visited.has(neighbor)) {
                    queue.push(neighbor);
                }
            }
        }

        return result;
    }

    dfs(start) {
        if (!this.nodes.has(start)) return [];

        const visited = new Set();
        const result = [];

        const dfsRecursive = (node) => {
            if (visited.has(node)) return;
            visited.add(node);
            result.push(node);

            const neighbors = this.adjacency.get(node) || [];
            for (const { target: neighbor } of neighbors) {
                dfsRecursive(neighbor);
            }
        };

        dfsRecursive(start);
        return result;
    }

    topologicalSort() {
        const inDegree = new Map();
        for (const node of this.nodes) {
            inDegree.set(node, 0);
        }

        for (const node of this.nodes) {
            const neighbors = this.adjacency.get(node) || [];
            for (const { target: neighbor } of neighbors) {
                inDegree.set(neighbor, (inDegree.get(neighbor) || 0) + 1);
            }
        }

        const queue = [];
        for (const [node, degree] of inDegree) {
            if (degree === 0) queue.push(node);
        }

        const result = [];
        while (queue.length > 0) {
            const node = queue.shift();
            result.push(node);

            const neighbors = this.adjacency.get(node) || [];
            for (const { target: neighbor } of neighbors) {
                inDegree.set(neighbor, inDegree.get(neighbor) - 1);
                if (inDegree.get(neighbor) === 0) {
                    queue.push(neighbor);
                }
            }
        }

        if (result.length !== this.nodes.size) {
            throw new Error("Graph contains a cycle");
        }

        return result;
    }
}

// =============================================================================
// Binary Search Tree
// =============================================================================

class TreeNode {
    constructor(value) {
        this.value = value;
        this.left = null;
        this.right = null;
    }
}

class BinarySearchTree {
    constructor(compareFn = (a, b) => a - b) {
        this.root = null;
        this.compare = compareFn;
        this._size = 0;
    }

    get size() {
        return this._size;
    }

    insert(value) {
        if (this.root === null) {
            this.root = new TreeNode(value);
            this._size++;
            return;
        }

        let current = this.root;
        while (true) {
            const cmp = this.compare(value, current.value);
            if (cmp < 0) {
                if (current.left === null) {
                    current.left = new TreeNode(value);
                    this._size++;
                    return;
                }
                current = current.left;
            } else if (cmp > 0) {
                if (current.right === null) {
                    current.right = new TreeNode(value);
                    this._size++;
                    return;
                }
                current = current.right;
            } else {
                return;
            }
        }
    }

    search(value) {
        let current = this.root;
        while (current !== null) {
            const cmp = this.compare(value, current.value);
            if (cmp < 0) {
                current = current.left;
            } else if (cmp > 0) {
                current = current.right;
            } else {
                return true;
            }
        }
        return false;
    }

    delete(value) {
        const deleteRecursive = (node, value) => {
            if (node === null) return { node: null, deleted: false };

            const cmp = this.compare(value, node.value);
            if (cmp < 0) {
                const result = deleteRecursive(node.left, value);
                node.left = result.node;
                return { node, deleted: result.deleted };
            } else if (cmp > 0) {
                const result = deleteRecursive(node.right, value);
                node.right = result.node;
                return { node, deleted: result.deleted };
            } else {
                if (node.left === null) return { node: node.right, deleted: true };
                if (node.right === null) return { node: node.left, deleted: true };

                let minNode = node.right;
                while (minNode.left !== null) {
                    minNode = minNode.left;
                }
                node.value = minNode.value;
                const result = deleteRecursive(node.right, minNode.value);
                node.right = result.node;
                return { node, deleted: true };
            }
        };

        const result = deleteRecursive(this.root, value);
        this.root = result.node;
        if (result.deleted) this._size--;
        return result.deleted;
    }

    inorder() {
        const result = [];
        const traverse = (node) => {
            if (node === null) return;
            traverse(node.left);
            result.push(node.value);
            traverse(node.right);
        };
        traverse(this.root);
        return result;
    }

    height() {
        const heightRecursive = (node) => {
            if (node === null) return 0;
            return 1 + Math.max(heightRecursive(node.left), heightRecursive(node.right));
        };
        return heightRecursive(this.root);
    }

    isBalanced() {
        const checkBalanced = (node) => {
            if (node === null) return { balanced: true, height: 0 };

            const left = checkBalanced(node.left);
            if (!left.balanced) return { balanced: false, height: 0 };

            const right = checkBalanced(node.right);
            if (!right.balanced) return { balanced: false, height: 0 };

            const balanced = Math.abs(left.height - right.height) <= 1;
            const height = 1 + Math.max(left.height, right.height);
            return { balanced, height };
        };
        return checkBalanced(this.root).balanced;
    }
}

// =============================================================================
// Sorting Algorithms
// =============================================================================

function quickSort(arr, low = 0, high = arr.length - 1) {
    if (low < high) {
        const pivotIdx = partition(arr, low, high);
        quickSort(arr, low, pivotIdx - 1);
        quickSort(arr, pivotIdx + 1, high);
    }
    return arr;
}

function partition(arr, low, high) {
    const pivot = arr[high];
    let i = low - 1;

    for (let j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
    }

    [arr[i + 1], arr[high]] = [arr[high], arr[i + 1]];
    return i + 1;
}

function mergeSort(arr) {
    if (arr.length <= 1) return arr.slice();

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

function heapSort(arr) {
    const n = arr.length;

    const heapify = (n, i) => {
        let largest = i;
        const left = 2 * i + 1;
        const right = 2 * i + 2;

        if (left < n && arr[left] > arr[largest]) largest = left;
        if (right < n && arr[right] > arr[largest]) largest = right;

        if (largest !== i) {
            [arr[i], arr[largest]] = [arr[largest], arr[i]];
            heapify(n, largest);
        }
    };

    for (let i = Math.floor(n / 2) - 1; i >= 0; i--) {
        heapify(n, i);
    }

    for (let i = n - 1; i > 0; i--) {
        [arr[0], arr[i]] = [arr[i], arr[0]];
        heapify(i, 0);
    }

    return arr;
}

// =============================================================================
// Dynamic Programming
// =============================================================================

function longestCommonSubsequence(s1, s2) {
    const m = s1.length, n = s2.length;
    const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (s1[i - 1] === s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    let lcs = "";
    let i = m, j = n;
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

function editDistance(s1, s2) {
    const m = s1.length, n = s2.length;
    const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;

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

function knapsack(weights, values, capacity) {
    const n = weights.length;
    const dp = Array(n + 1).fill(null).map(() => Array(capacity + 1).fill(0));

    for (let i = 1; i <= n; i++) {
        for (let w = 0; w <= capacity; w++) {
            if (weights[i - 1] <= w) {
                dp[i][w] = Math.max(dp[i - 1][w], dp[i - 1][w - weights[i - 1]] + values[i - 1]);
            } else {
                dp[i][w] = dp[i - 1][w];
            }
        }
    }

    const items = [];
    let w = capacity;
    for (let i = n; i > 0; i--) {
        if (dp[i][w] !== dp[i - 1][w]) {
            items.push(i - 1);
            w -= weights[i - 1];
        }
    }
    items.reverse();

    return { value: dp[n][capacity], items };
}

function coinChange(coins, amount) {
    const dp = Array(amount + 1).fill(Infinity);
    dp[0] = 0;

    for (const coin of coins) {
        for (let x = coin; x <= amount; x++) {
            dp[x] = Math.min(dp[x], dp[x - coin] + 1);
        }
    }

    return dp[amount] === Infinity ? -1 : dp[amount];
}

// =============================================================================
// String Algorithms
// =============================================================================

function kmpSearch(text, pattern) {
    if (!pattern) return [];

    const buildFailureTable = (pattern) => {
        const m = pattern.length;
        const failure = Array(m).fill(0);
        let j = 0;

        for (let i = 1; i < m; i++) {
            while (j > 0 && pattern[i] !== pattern[j]) {
                j = failure[j - 1];
            }
            if (pattern[i] === pattern[j]) j++;
            failure[i] = j;
        }

        return failure;
    };

    const failure = buildFailureTable(pattern);
    const matches = [];
    let j = 0;

    for (let i = 0; i < text.length; i++) {
        while (j > 0 && text[i] !== pattern[j]) {
            j = failure[j - 1];
        }
        if (text[i] === pattern[j]) j++;
        if (j === pattern.length) {
            matches.push(i - j + 1);
            j = failure[j - 1];
        }
    }

    return matches;
}

// =============================================================================
// Main
// =============================================================================

function main() {
    console.log("=== Graph Algorithms ===");
    const g = new Graph();
    g.addEdge("A", "B", 1);
    g.addEdge("A", "C", 4);
    g.addEdge("B", "C", 2);
    g.addEdge("B", "D", 5);
    g.addEdge("C", "D", 1);
    console.log("BFS:", g.bfs("A"));
    console.log("DFS:", g.dfs("A"));
    const { distance, path } = g.dijkstra("A", "D");
    console.log(`Shortest A->D: ${path.join(" -> ")}, distance: ${distance}`);

    console.log("\n=== Tree Algorithms ===");
    const bst = new BinarySearchTree();
    [5, 3, 7, 1, 4, 6, 8].forEach(x => bst.insert(x));
    console.log("Inorder:", bst.inorder());
    console.log("Height:", bst.height());
    console.log("Balanced:", bst.isBalanced());

    console.log("\n=== Sorting Algorithms ===");
    console.log("QuickSort:", quickSort([64, 34, 25, 12, 22, 11, 90]));
    console.log("MergeSort:", mergeSort([64, 34, 25, 12, 22, 11, 90]));
    console.log("HeapSort:", heapSort([64, 34, 25, 12, 22, 11, 90]));

    console.log("\n=== Dynamic Programming ===");
    console.log("LCS('ABCDGH', 'AEDFHR'):", longestCommonSubsequence("ABCDGH", "AEDFHR"));
    console.log("Edit distance('kitten', 'sitting'):", editDistance("kitten", "sitting"));
    console.log("Coin change([1,2,5], 11):", coinChange([1, 2, 5], 11));
    const ks = knapsack([10, 20, 30], [60, 100, 120], 50);
    console.log(`Knapsack: value=${ks.value}, items=${ks.items}`);

    console.log("\n=== String Algorithms ===");
    console.log("KMP search:", kmpSearch("AABAACAADAABAAABAA", "AABA"));
}

main();

module.exports = {
    Graph,
    BinarySearchTree,
    quickSort,
    mergeSort,
    heapSort,
    longestCommonSubsequence,
    editDistance,
    knapsack,
    coinChange,
    kmpSearch
};

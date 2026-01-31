#!/usr/bin/env python3
"""
Massive Python file with high complexity (500+ LOC, CCN 30+).
This file contains complex algorithms and data structures.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar
import heapq
import math
from collections import defaultdict, deque

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


# =============================================================================
# Graph Algorithms
# =============================================================================

class Graph(Generic[T]):
    """Weighted directed graph implementation."""

    def __init__(self):
        self._adjacency: Dict[T, List[Tuple[T, float]]] = defaultdict(list)
        self._nodes: Set[T] = set()

    def add_node(self, node: T) -> None:
        self._nodes.add(node)
        if node not in self._adjacency:
            self._adjacency[node] = []

    def add_edge(self, source: T, target: T, weight: float = 1.0) -> None:
        self.add_node(source)
        self.add_node(target)
        self._adjacency[source].append((target, weight))

    def neighbors(self, node: T) -> List[Tuple[T, float]]:
        return self._adjacency.get(node, [])

    def nodes(self) -> Set[T]:
        return self._nodes.copy()

    def dijkstra(self, start: T, end: T) -> Tuple[float, List[T]]:
        """Find shortest path using Dijkstra's algorithm."""
        if start not in self._nodes or end not in self._nodes:
            return float("inf"), []

        distances: Dict[T, float] = {node: float("inf") for node in self._nodes}
        distances[start] = 0
        previous: Dict[T, Optional[T]] = {node: None for node in self._nodes}
        heap: List[Tuple[float, T]] = [(0, start)]
        visited: Set[T] = set()

        while heap:
            current_dist, current = heapq.heappop(heap)

            if current in visited:
                continue

            if current == end:
                path = []
                node: Optional[T] = end
                while node is not None:
                    path.append(node)
                    node = previous[node]
                return current_dist, list(reversed(path))

            visited.add(current)

            for neighbor, weight in self._adjacency[current]:
                if neighbor in visited:
                    continue

                new_dist = current_dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(heap, (new_dist, neighbor))

        return float("inf"), []

    def bfs(self, start: T) -> List[T]:
        """Breadth-first search traversal."""
        if start not in self._nodes:
            return []

        visited: Set[T] = set()
        queue: deque[T] = deque([start])
        result: List[T] = []

        while queue:
            node = queue.popleft()
            if node in visited:
                continue

            visited.add(node)
            result.append(node)

            for neighbor, _ in self._adjacency[node]:
                if neighbor not in visited:
                    queue.append(neighbor)

        return result

    def dfs(self, start: T) -> List[T]:
        """Depth-first search traversal."""
        if start not in self._nodes:
            return []

        visited: Set[T] = set()
        result: List[T] = []

        def _dfs_recursive(node: T) -> None:
            if node in visited:
                return
            visited.add(node)
            result.append(node)
            for neighbor, _ in self._adjacency[node]:
                _dfs_recursive(neighbor)

        _dfs_recursive(start)
        return result

    def topological_sort(self) -> List[T]:
        """Topological sort using Kahn's algorithm."""
        in_degree: Dict[T, int] = {node: 0 for node in self._nodes}

        for node in self._nodes:
            for neighbor, _ in self._adjacency[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        queue: deque[T] = deque([n for n in self._nodes if in_degree[n] == 0])
        result: List[T] = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for neighbor, _ in self._adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._nodes):
            raise ValueError("Graph contains a cycle")

        return result

    def strongly_connected_components(self) -> List[List[T]]:
        """Find SCCs using Kosaraju's algorithm."""
        visited: Set[T] = set()
        finish_order: List[T] = []

        def _dfs1(node: T) -> None:
            if node in visited:
                return
            visited.add(node)
            for neighbor, _ in self._adjacency[node]:
                _dfs1(neighbor)
            finish_order.append(node)

        for node in self._nodes:
            _dfs1(node)

        reversed_graph: Dict[T, List[T]] = defaultdict(list)
        for node in self._nodes:
            for neighbor, _ in self._adjacency[node]:
                reversed_graph[neighbor].append(node)

        visited.clear()
        sccs: List[List[T]] = []

        def _dfs2(node: T, component: List[T]) -> None:
            if node in visited:
                return
            visited.add(node)
            component.append(node)
            for neighbor in reversed_graph[node]:
                _dfs2(neighbor, component)

        for node in reversed(finish_order):
            if node not in visited:
                component: List[T] = []
                _dfs2(node, component)
                sccs.append(component)

        return sccs


# =============================================================================
# Tree Algorithms
# =============================================================================

@dataclass
class TreeNode(Generic[T]):
    """Binary tree node."""
    value: T
    left: Optional["TreeNode[T]"] = None
    right: Optional["TreeNode[T]"] = None


class BinarySearchTree(Generic[T]):
    """Binary search tree implementation."""

    def __init__(self, compare: Optional[Callable[[T, T], int]] = None):
        self._root: Optional[TreeNode[T]] = None
        self._compare = compare or (lambda a, b: (a > b) - (a < b))
        self._size = 0

    def insert(self, value: T) -> None:
        if self._root is None:
            self._root = TreeNode(value)
            self._size += 1
            return

        current = self._root
        while True:
            cmp = self._compare(value, current.value)
            if cmp < 0:
                if current.left is None:
                    current.left = TreeNode(value)
                    self._size += 1
                    return
                current = current.left
            elif cmp > 0:
                if current.right is None:
                    current.right = TreeNode(value)
                    self._size += 1
                    return
                current = current.right
            else:
                return

    def search(self, value: T) -> bool:
        current = self._root
        while current is not None:
            cmp = self._compare(value, current.value)
            if cmp < 0:
                current = current.left
            elif cmp > 0:
                current = current.right
            else:
                return True
        return False

    def delete(self, value: T) -> bool:
        def _find_min(node: TreeNode[T]) -> TreeNode[T]:
            while node.left is not None:
                node = node.left
            return node

        def _delete_recursive(node: Optional[TreeNode[T]], value: T) -> Tuple[Optional[TreeNode[T]], bool]:
            if node is None:
                return None, False

            cmp = self._compare(value, node.value)
            if cmp < 0:
                node.left, deleted = _delete_recursive(node.left, value)
                return node, deleted
            elif cmp > 0:
                node.right, deleted = _delete_recursive(node.right, value)
                return node, deleted
            else:
                if node.left is None:
                    return node.right, True
                elif node.right is None:
                    return node.left, True
                else:
                    min_node = _find_min(node.right)
                    node.value = min_node.value
                    node.right, _ = _delete_recursive(node.right, min_node.value)
                    return node, True

        self._root, deleted = _delete_recursive(self._root, value)
        if deleted:
            self._size -= 1
        return deleted

    def inorder(self) -> List[T]:
        result: List[T] = []

        def _traverse(node: Optional[TreeNode[T]]) -> None:
            if node is None:
                return
            _traverse(node.left)
            result.append(node.value)
            _traverse(node.right)

        _traverse(self._root)
        return result

    def height(self) -> int:
        def _height(node: Optional[TreeNode[T]]) -> int:
            if node is None:
                return 0
            return 1 + max(_height(node.left), _height(node.right))

        return _height(self._root)

    def is_balanced(self) -> bool:
        def _check_balanced(node: Optional[TreeNode[T]]) -> Tuple[bool, int]:
            if node is None:
                return True, 0

            left_balanced, left_height = _check_balanced(node.left)
            if not left_balanced:
                return False, 0

            right_balanced, right_height = _check_balanced(node.right)
            if not right_balanced:
                return False, 0

            balanced = abs(left_height - right_height) <= 1
            height = 1 + max(left_height, right_height)
            return balanced, height

        balanced, _ = _check_balanced(self._root)
        return balanced


# =============================================================================
# Sorting Algorithms
# =============================================================================

def quicksort(arr: List[T], low: int = 0, high: Optional[int] = None) -> List[T]:
    """In-place quicksort implementation."""
    if high is None:
        high = len(arr) - 1
        arr = arr.copy()

    def _partition(low: int, high: int) -> int:
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1

    if low < high:
        pivot_idx = _partition(low, high)
        quicksort(arr, low, pivot_idx - 1)
        quicksort(arr, pivot_idx + 1, high)

    return arr


def mergesort(arr: List[T]) -> List[T]:
    """Merge sort implementation."""
    if len(arr) <= 1:
        return arr.copy()

    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])

    result: List[T] = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


def heapsort(arr: List[T]) -> List[T]:
    """Heap sort implementation."""
    arr = arr.copy()
    n = len(arr)

    def _heapify(n: int, i: int) -> None:
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2

        if left < n and arr[left] > arr[largest]:
            largest = left

        if right < n and arr[right] > arr[largest]:
            largest = right

        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            _heapify(n, largest)

    for i in range(n // 2 - 1, -1, -1):
        _heapify(n, i)

    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        _heapify(i, 0)

    return arr


# =============================================================================
# Dynamic Programming
# =============================================================================

def longest_common_subsequence(s1: str, s2: str) -> str:
    """Find the longest common subsequence of two strings."""
    m, n = len(s1), len(s2)
    dp: List[List[int]] = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs: List[str] = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    return "".join(reversed(lcs))


def knapsack(weights: List[int], values: List[int], capacity: int) -> Tuple[int, List[int]]:
    """0/1 knapsack problem with item selection."""
    n = len(weights)
    dp: List[List[int]] = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i - 1] <= w:
                dp[i][w] = max(
                    dp[i - 1][w],
                    dp[i - 1][w - weights[i - 1]] + values[i - 1]
                )
            else:
                dp[i][w] = dp[i - 1][w]

    items: List[int] = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            items.append(i - 1)
            w -= weights[i - 1]

    return dp[n][capacity], list(reversed(items))


def edit_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    m, n = len(s1), len(s2)
    dp: List[List[int]] = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],
                    dp[i][j - 1],
                    dp[i - 1][j - 1]
                )

    return dp[m][n]


def coin_change(coins: List[int], amount: int) -> int:
    """Find minimum number of coins to make the amount."""
    dp: List[int] = [float("inf")] * (amount + 1)
    dp[0] = 0

    for coin in coins:
        for x in range(coin, amount + 1):
            dp[x] = min(dp[x], dp[x - coin] + 1)

    return dp[amount] if dp[amount] != float("inf") else -1


# =============================================================================
# String Algorithms
# =============================================================================

def kmp_search(text: str, pattern: str) -> List[int]:
    """KMP string matching algorithm."""
    if not pattern:
        return []

    def _build_failure_table(pattern: str) -> List[int]:
        m = len(pattern)
        failure: List[int] = [0] * m
        j = 0

        for i in range(1, m):
            while j > 0 and pattern[i] != pattern[j]:
                j = failure[j - 1]
            if pattern[i] == pattern[j]:
                j += 1
            failure[i] = j

        return failure

    failure = _build_failure_table(pattern)
    matches: List[int] = []
    j = 0

    for i in range(len(text)):
        while j > 0 and text[i] != pattern[j]:
            j = failure[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == len(pattern):
            matches.append(i - j + 1)
            j = failure[j - 1]

    return matches


def rabin_karp_search(text: str, pattern: str, base: int = 256, mod: int = 101) -> List[int]:
    """Rabin-Karp string matching algorithm."""
    m, n = len(pattern), len(text)
    if m > n:
        return []

    h = pow(base, m - 1, mod)
    pattern_hash = 0
    text_hash = 0

    for i in range(m):
        pattern_hash = (base * pattern_hash + ord(pattern[i])) % mod
        text_hash = (base * text_hash + ord(text[i])) % mod

    matches: List[int] = []

    for i in range(n - m + 1):
        if pattern_hash == text_hash:
            if text[i:i + m] == pattern:
                matches.append(i)

        if i < n - m:
            text_hash = (base * (text_hash - ord(text[i]) * h) + ord(text[i + m])) % mod
            if text_hash < 0:
                text_hash += mod

    return matches


# =============================================================================
# Main
# =============================================================================

def main():
    print("=== Graph Algorithms ===")
    g = Graph[str]()
    g.add_edge("A", "B", 1)
    g.add_edge("A", "C", 4)
    g.add_edge("B", "C", 2)
    g.add_edge("B", "D", 5)
    g.add_edge("C", "D", 1)
    print(f"BFS: {g.bfs('A')}")
    print(f"DFS: {g.dfs('A')}")
    dist, path = g.dijkstra("A", "D")
    print(f"Shortest path A->D: {path}, distance: {dist}")

    print("\n=== Tree Algorithms ===")
    bst = BinarySearchTree[int]()
    for x in [5, 3, 7, 1, 4, 6, 8]:
        bst.insert(x)
    print(f"Inorder: {bst.inorder()}")
    print(f"Height: {bst.height()}")
    print(f"Balanced: {bst.is_balanced()}")

    print("\n=== Sorting Algorithms ===")
    arr = [64, 34, 25, 12, 22, 11, 90]
    print(f"Quicksort: {quicksort(arr)}")
    print(f"Mergesort: {mergesort(arr)}")
    print(f"Heapsort: {heapsort(arr)}")

    print("\n=== Dynamic Programming ===")
    print(f"LCS('ABCDGH', 'AEDFHR'): {longest_common_subsequence('ABCDGH', 'AEDFHR')}")
    print(f"Edit distance('kitten', 'sitting'): {edit_distance('kitten', 'sitting')}")
    print(f"Coin change([1,2,5], 11): {coin_change([1, 2, 5], 11)}")
    value, items = knapsack([10, 20, 30], [60, 100, 120], 50)
    print(f"Knapsack: value={value}, items={items}")

    print("\n=== String Algorithms ===")
    print(f"KMP search: {kmp_search('AABAACAADAABAAABAA', 'AABA')}")
    print(f"Rabin-Karp: {rabin_karp_search('AABAACAADAABAAABAA', 'AABA')}")


if __name__ == "__main__":
    main()

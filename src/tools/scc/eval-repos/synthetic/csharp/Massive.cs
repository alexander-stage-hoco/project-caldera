using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace Synthetic
{
    /// <summary>
    /// Massive C# file with high complexity (500+ LOC, CCN 30+).
    /// Contains complex algorithms and data structures.
    /// </summary>
    public class Massive
    {
        // =====================================================================
        // Graph Implementation
        // =====================================================================

        public class Graph<T> where T : IEquatable<T>
        {
            private readonly Dictionary<T, List<(T Target, double Weight)>> _adjacency = new();
            private readonly HashSet<T> _nodes = new();

            public void AddNode(T node)
            {
                _nodes.Add(node);
                if (!_adjacency.ContainsKey(node))
                    _adjacency[node] = new List<(T, double)>();
            }

            public void AddEdge(T source, T target, double weight = 1.0)
            {
                AddNode(source);
                AddNode(target);
                _adjacency[source].Add((target, weight));
            }

            public (double Distance, List<T> Path) Dijkstra(T start, T end)
            {
                if (!_nodes.Contains(start) || !_nodes.Contains(end))
                    return (double.MaxValue, new List<T>());

                var distances = _nodes.ToDictionary(n => n, _ => double.MaxValue);
                distances[start] = 0;

                var previous = _nodes.ToDictionary(n => n, _ => default(T));
                var heap = new SortedSet<(double Dist, T Node)>(
                    Comparer<(double, T)>.Create((a, b) =>
                        a.Item1 != b.Item1 ? a.Item1.CompareTo(b.Item1) : a.Item2.GetHashCode().CompareTo(b.Item2.GetHashCode()))
                );
                heap.Add((0, start));
                var visited = new HashSet<T>();

                while (heap.Count > 0)
                {
                    var (currentDist, current) = heap.Min;
                    heap.Remove(heap.Min);

                    if (visited.Contains(current))
                        continue;

                    if (current.Equals(end))
                    {
                        var path = new List<T>();
                        var node = end;
                        while (node != null && !node.Equals(default(T)))
                        {
                            path.Add(node);
                            node = previous[node];
                        }
                        path.Reverse();
                        return (currentDist, path);
                    }

                    visited.Add(current);

                    if (_adjacency.TryGetValue(current, out var neighbors))
                    {
                        foreach (var (neighbor, weight) in neighbors)
                        {
                            if (visited.Contains(neighbor))
                                continue;

                            var newDist = currentDist + weight;
                            if (newDist < distances[neighbor])
                            {
                                distances[neighbor] = newDist;
                                previous[neighbor] = current;
                                heap.Add((newDist, neighbor));
                            }
                        }
                    }
                }

                return (double.MaxValue, new List<T>());
            }

            public List<T> BreadthFirstSearch(T start)
            {
                if (!_nodes.Contains(start))
                    return new List<T>();

                var visited = new HashSet<T>();
                var queue = new Queue<T>();
                var result = new List<T>();

                queue.Enqueue(start);

                while (queue.Count > 0)
                {
                    var node = queue.Dequeue();
                    if (visited.Contains(node))
                        continue;

                    visited.Add(node);
                    result.Add(node);

                    if (_adjacency.TryGetValue(node, out var neighbors))
                    {
                        foreach (var (neighbor, _) in neighbors)
                        {
                            if (!visited.Contains(neighbor))
                                queue.Enqueue(neighbor);
                        }
                    }
                }

                return result;
            }

            public List<T> DepthFirstSearch(T start)
            {
                if (!_nodes.Contains(start))
                    return new List<T>();

                var visited = new HashSet<T>();
                var result = new List<T>();

                void Dfs(T node)
                {
                    if (visited.Contains(node))
                        return;

                    visited.Add(node);
                    result.Add(node);

                    if (_adjacency.TryGetValue(node, out var neighbors))
                    {
                        foreach (var (neighbor, _) in neighbors)
                            Dfs(neighbor);
                    }
                }

                Dfs(start);
                return result;
            }

            public List<T> TopologicalSort()
            {
                var inDegree = _nodes.ToDictionary(n => n, _ => 0);

                foreach (var node in _nodes)
                {
                    if (_adjacency.TryGetValue(node, out var neighbors))
                    {
                        foreach (var (neighbor, _) in neighbors)
                            inDegree[neighbor]++;
                    }
                }

                var queue = new Queue<T>(inDegree.Where(kv => kv.Value == 0).Select(kv => kv.Key));
                var result = new List<T>();

                while (queue.Count > 0)
                {
                    var node = queue.Dequeue();
                    result.Add(node);

                    if (_adjacency.TryGetValue(node, out var neighbors))
                    {
                        foreach (var (neighbor, _) in neighbors)
                        {
                            inDegree[neighbor]--;
                            if (inDegree[neighbor] == 0)
                                queue.Enqueue(neighbor);
                        }
                    }
                }

                if (result.Count != _nodes.Count)
                    throw new InvalidOperationException("Graph contains a cycle");

                return result;
            }
        }

        // =====================================================================
        // Binary Search Tree
        // =====================================================================

        public class TreeNode<T>
        {
            public T Value { get; set; }
            public TreeNode<T> Left { get; set; }
            public TreeNode<T> Right { get; set; }

            public TreeNode(T value)
            {
                Value = value;
            }
        }

        public class BinarySearchTree<T> where T : IComparable<T>
        {
            private TreeNode<T> _root;
            private int _size;

            public int Size => _size;

            public void Insert(T value)
            {
                if (_root == null)
                {
                    _root = new TreeNode<T>(value);
                    _size++;
                    return;
                }

                var current = _root;
                while (true)
                {
                    var cmp = value.CompareTo(current.Value);
                    if (cmp < 0)
                    {
                        if (current.Left == null)
                        {
                            current.Left = new TreeNode<T>(value);
                            _size++;
                            return;
                        }
                        current = current.Left;
                    }
                    else if (cmp > 0)
                    {
                        if (current.Right == null)
                        {
                            current.Right = new TreeNode<T>(value);
                            _size++;
                            return;
                        }
                        current = current.Right;
                    }
                    else
                    {
                        return;
                    }
                }
            }

            public bool Search(T value)
            {
                var current = _root;
                while (current != null)
                {
                    var cmp = value.CompareTo(current.Value);
                    if (cmp < 0)
                        current = current.Left;
                    else if (cmp > 0)
                        current = current.Right;
                    else
                        return true;
                }
                return false;
            }

            public bool Delete(T value)
            {
                _root = DeleteRecursive(_root, value, out var deleted);
                if (deleted) _size--;
                return deleted;
            }

            private TreeNode<T> DeleteRecursive(TreeNode<T> node, T value, out bool deleted)
            {
                deleted = false;
                if (node == null)
                    return null;

                var cmp = value.CompareTo(node.Value);
                if (cmp < 0)
                {
                    node.Left = DeleteRecursive(node.Left, value, out deleted);
                }
                else if (cmp > 0)
                {
                    node.Right = DeleteRecursive(node.Right, value, out deleted);
                }
                else
                {
                    deleted = true;
                    if (node.Left == null)
                        return node.Right;
                    if (node.Right == null)
                        return node.Left;

                    var minNode = FindMin(node.Right);
                    node.Value = minNode.Value;
                    node.Right = DeleteRecursive(node.Right, minNode.Value, out _);
                }
                return node;
            }

            private TreeNode<T> FindMin(TreeNode<T> node)
            {
                while (node.Left != null)
                    node = node.Left;
                return node;
            }

            public List<T> InorderTraversal()
            {
                var result = new List<T>();
                Inorder(_root, result);
                return result;
            }

            private void Inorder(TreeNode<T> node, List<T> result)
            {
                if (node == null) return;
                Inorder(node.Left, result);
                result.Add(node.Value);
                Inorder(node.Right, result);
            }

            public int Height()
            {
                return HeightRecursive(_root);
            }

            private int HeightRecursive(TreeNode<T> node)
            {
                if (node == null) return 0;
                return 1 + Math.Max(HeightRecursive(node.Left), HeightRecursive(node.Right));
            }

            public bool IsBalanced()
            {
                return CheckBalanced(_root).Balanced;
            }

            private (bool Balanced, int Height) CheckBalanced(TreeNode<T> node)
            {
                if (node == null)
                    return (true, 0);

                var left = CheckBalanced(node.Left);
                if (!left.Balanced)
                    return (false, 0);

                var right = CheckBalanced(node.Right);
                if (!right.Balanced)
                    return (false, 0);

                var balanced = Math.Abs(left.Height - right.Height) <= 1;
                var height = 1 + Math.Max(left.Height, right.Height);
                return (balanced, height);
            }
        }

        // =====================================================================
        // Sorting Algorithms
        // =====================================================================

        public static class Sorting
        {
            public static void QuickSort<T>(T[] arr) where T : IComparable<T>
            {
                QuickSortRecursive(arr, 0, arr.Length - 1);
            }

            private static void QuickSortRecursive<T>(T[] arr, int low, int high) where T : IComparable<T>
            {
                if (low < high)
                {
                    var pivotIdx = Partition(arr, low, high);
                    QuickSortRecursive(arr, low, pivotIdx - 1);
                    QuickSortRecursive(arr, pivotIdx + 1, high);
                }
            }

            private static int Partition<T>(T[] arr, int low, int high) where T : IComparable<T>
            {
                var pivot = arr[high];
                var i = low - 1;

                for (var j = low; j < high; j++)
                {
                    if (arr[j].CompareTo(pivot) <= 0)
                    {
                        i++;
                        (arr[i], arr[j]) = (arr[j], arr[i]);
                    }
                }

                (arr[i + 1], arr[high]) = (arr[high], arr[i + 1]);
                return i + 1;
            }

            public static T[] MergeSort<T>(T[] arr) where T : IComparable<T>
            {
                if (arr.Length <= 1)
                    return arr.ToArray();

                var mid = arr.Length / 2;
                var left = MergeSort(arr.Take(mid).ToArray());
                var right = MergeSort(arr.Skip(mid).ToArray());

                return Merge(left, right);
            }

            private static T[] Merge<T>(T[] left, T[] right) where T : IComparable<T>
            {
                var result = new T[left.Length + right.Length];
                int i = 0, j = 0, k = 0;

                while (i < left.Length && j < right.Length)
                {
                    if (left[i].CompareTo(right[j]) <= 0)
                        result[k++] = left[i++];
                    else
                        result[k++] = right[j++];
                }

                while (i < left.Length)
                    result[k++] = left[i++];

                while (j < right.Length)
                    result[k++] = right[j++];

                return result;
            }

            public static void HeapSort<T>(T[] arr) where T : IComparable<T>
            {
                var n = arr.Length;

                for (var i = n / 2 - 1; i >= 0; i--)
                    Heapify(arr, n, i);

                for (var i = n - 1; i > 0; i--)
                {
                    (arr[0], arr[i]) = (arr[i], arr[0]);
                    Heapify(arr, i, 0);
                }
            }

            private static void Heapify<T>(T[] arr, int n, int i) where T : IComparable<T>
            {
                var largest = i;
                var left = 2 * i + 1;
                var right = 2 * i + 2;

                if (left < n && arr[left].CompareTo(arr[largest]) > 0)
                    largest = left;

                if (right < n && arr[right].CompareTo(arr[largest]) > 0)
                    largest = right;

                if (largest != i)
                {
                    (arr[i], arr[largest]) = (arr[largest], arr[i]);
                    Heapify(arr, n, largest);
                }
            }
        }

        // =====================================================================
        // Dynamic Programming
        // =====================================================================

        public static class DynamicProgramming
        {
            public static string LongestCommonSubsequence(string s1, string s2)
            {
                var m = s1.Length;
                var n = s2.Length;
                var dp = new int[m + 1, n + 1];

                for (var i = 1; i <= m; i++)
                {
                    for (var j = 1; j <= n; j++)
                    {
                        if (s1[i - 1] == s2[j - 1])
                            dp[i, j] = dp[i - 1, j - 1] + 1;
                        else
                            dp[i, j] = Math.Max(dp[i - 1, j], dp[i, j - 1]);
                    }
                }

                var sb = new StringBuilder();
                int x = m, y = n;
                while (x > 0 && y > 0)
                {
                    if (s1[x - 1] == s2[y - 1])
                    {
                        sb.Insert(0, s1[x - 1]);
                        x--;
                        y--;
                    }
                    else if (dp[x - 1, y] > dp[x, y - 1])
                    {
                        x--;
                    }
                    else
                    {
                        y--;
                    }
                }

                return sb.ToString();
            }

            public static int EditDistance(string s1, string s2)
            {
                var m = s1.Length;
                var n = s2.Length;
                var dp = new int[m + 1, n + 1];

                for (var i = 0; i <= m; i++)
                    dp[i, 0] = i;
                for (var j = 0; j <= n; j++)
                    dp[0, j] = j;

                for (var i = 1; i <= m; i++)
                {
                    for (var j = 1; j <= n; j++)
                    {
                        if (s1[i - 1] == s2[j - 1])
                            dp[i, j] = dp[i - 1, j - 1];
                        else
                            dp[i, j] = 1 + Math.Min(
                                dp[i - 1, j],
                                Math.Min(dp[i, j - 1], dp[i - 1, j - 1])
                            );
                    }
                }

                return dp[m, n];
            }

            public static (int Value, List<int> Items) Knapsack(int[] weights, int[] values, int capacity)
            {
                var n = weights.Length;
                var dp = new int[n + 1, capacity + 1];

                for (var i = 1; i <= n; i++)
                {
                    for (var w = 0; w <= capacity; w++)
                    {
                        if (weights[i - 1] <= w)
                            dp[i, w] = Math.Max(dp[i - 1, w], dp[i - 1, w - weights[i - 1]] + values[i - 1]);
                        else
                            dp[i, w] = dp[i - 1, w];
                    }
                }

                var items = new List<int>();
                var wt = capacity;
                for (var i = n; i > 0; i--)
                {
                    if (dp[i, wt] != dp[i - 1, wt])
                    {
                        items.Add(i - 1);
                        wt -= weights[i - 1];
                    }
                }
                items.Reverse();

                return (dp[n, capacity], items);
            }

            public static int CoinChange(int[] coins, int amount)
            {
                var dp = new int[amount + 1];
                Array.Fill(dp, int.MaxValue);
                dp[0] = 0;

                foreach (var coin in coins)
                {
                    for (var x = coin; x <= amount; x++)
                    {
                        if (dp[x - coin] != int.MaxValue)
                            dp[x] = Math.Min(dp[x], dp[x - coin] + 1);
                    }
                }

                return dp[amount] == int.MaxValue ? -1 : dp[amount];
            }
        }

        // =====================================================================
        // Main
        // =====================================================================

        public static void Main(string[] args)
        {
            Console.WriteLine("=== Graph Algorithms ===");
            var g = new Graph<string>();
            g.AddEdge("A", "B", 1);
            g.AddEdge("A", "C", 4);
            g.AddEdge("B", "C", 2);
            g.AddEdge("B", "D", 5);
            g.AddEdge("C", "D", 1);
            Console.WriteLine($"BFS: {string.Join(", ", g.BreadthFirstSearch("A"))}");
            Console.WriteLine($"DFS: {string.Join(", ", g.DepthFirstSearch("A"))}");
            var (dist, path) = g.Dijkstra("A", "D");
            Console.WriteLine($"Shortest A->D: {string.Join(" -> ", path)}, distance: {dist}");

            Console.WriteLine("\n=== Tree Algorithms ===");
            var bst = new BinarySearchTree<int>();
            foreach (var x in new[] { 5, 3, 7, 1, 4, 6, 8 })
                bst.Insert(x);
            Console.WriteLine($"Inorder: {string.Join(", ", bst.InorderTraversal())}");
            Console.WriteLine($"Height: {bst.Height()}");
            Console.WriteLine($"Balanced: {bst.IsBalanced()}");

            Console.WriteLine("\n=== Sorting Algorithms ===");
            var arr = new[] { 64, 34, 25, 12, 22, 11, 90 };
            Sorting.QuickSort(arr);
            Console.WriteLine($"QuickSort: {string.Join(", ", arr)}");
            Console.WriteLine($"MergeSort: {string.Join(", ", Sorting.MergeSort(new[] { 64, 34, 25, 12, 22, 11, 90 }))}");

            Console.WriteLine("\n=== Dynamic Programming ===");
            Console.WriteLine($"LCS('ABCDGH', 'AEDFHR'): {DynamicProgramming.LongestCommonSubsequence("ABCDGH", "AEDFHR")}");
            Console.WriteLine($"Edit distance('kitten', 'sitting'): {DynamicProgramming.EditDistance("kitten", "sitting")}");
            Console.WriteLine($"Coin change([1,2,5], 11): {DynamicProgramming.CoinChange(new[] { 1, 2, 5 }, 11)}");
        }
    }
}

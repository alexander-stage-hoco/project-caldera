package synthetic;

import java.util.*;

/**
 * Massive Java file - High complexity (CCN ~30+), 500+ LOC.
 * Contains advanced Java patterns with complex logic.
 */
public class Massive {

    // ===== BINARY SEARCH TREE =====

    static class TreeNode<T> {
        T value;
        TreeNode<T> left;
        TreeNode<T> right;

        TreeNode(T value) {
            this.value = value;
        }
    }

    public static class BST<T extends Comparable<T>> {
        private TreeNode<T> root;

        public void insert(T value) {
            TreeNode<T> newNode = new TreeNode<>(value);

            if (root == null) {
                root = newNode;
                return;
            }

            TreeNode<T> current = root;
            while (true) {
                int cmp = value.compareTo(current.value);
                if (cmp < 0) {
                    if (current.left == null) {
                        current.left = newNode;
                        return;
                    }
                    current = current.left;
                } else if (cmp > 0) {
                    if (current.right == null) {
                        current.right = newNode;
                        return;
                    }
                    current = current.right;
                } else {
                    return; // Duplicate
                }
            }
        }

        public boolean find(T value) {
            TreeNode<T> current = root;
            while (current != null) {
                int cmp = value.compareTo(current.value);
                if (cmp == 0) {
                    return true;
                } else if (cmp < 0) {
                    current = current.left;
                } else {
                    current = current.right;
                }
            }
            return false;
        }

        public boolean delete(T value) {
            TreeNode<T> parent = null;
            TreeNode<T> current = root;
            boolean isLeft = false;

            while (current != null) {
                int cmp = value.compareTo(current.value);
                if (cmp == 0) {
                    break;
                }
                parent = current;
                if (cmp < 0) {
                    current = current.left;
                    isLeft = true;
                } else {
                    current = current.right;
                    isLeft = false;
                }
            }

            if (current == null) {
                return false;
            }

            // Leaf node
            if (current.left == null && current.right == null) {
                if (current == root) {
                    root = null;
                } else if (isLeft) {
                    parent.left = null;
                } else {
                    parent.right = null;
                }
            }
            // One child (left)
            else if (current.right == null) {
                if (current == root) {
                    root = current.left;
                } else if (isLeft) {
                    parent.left = current.left;
                } else {
                    parent.right = current.left;
                }
            }
            // One child (right)
            else if (current.left == null) {
                if (current == root) {
                    root = current.right;
                } else if (isLeft) {
                    parent.left = current.right;
                } else {
                    parent.right = current.right;
                }
            }
            // Two children
            else {
                T successor = findMin(current.right);
                current.value = successor;
                deleteMin(current, current.right);
            }

            return true;
        }

        private T findMin(TreeNode<T> node) {
            while (node.left != null) {
                node = node.left;
            }
            return node.value;
        }

        private void deleteMin(TreeNode<T> parent, TreeNode<T> node) {
            while (node.left != null) {
                parent = node;
                node = node.left;
            }
            if (parent.left == node) {
                parent.left = node.right;
            } else {
                parent.right = node.right;
            }
        }

        public List<T> inOrder() {
            List<T> result = new ArrayList<>();
            inOrderHelper(root, result);
            return result;
        }

        private void inOrderHelper(TreeNode<T> node, List<T> result) {
            if (node != null) {
                inOrderHelper(node.left, result);
                result.add(node.value);
                inOrderHelper(node.right, result);
            }
        }
    }

    // ===== GRAPH WITH DIJKSTRA =====

    public static class Edge {
        int to;
        int weight;

        Edge(int to, int weight) {
            this.to = to;
            this.weight = weight;
        }
    }

    public static class Graph {
        private final int vertices;
        private final Map<Integer, List<Edge>> edges;

        public Graph(int vertices) {
            this.vertices = vertices;
            this.edges = new HashMap<>();
        }

        public void addEdge(int from, int to, int weight) {
            edges.computeIfAbsent(from, k -> new ArrayList<>()).add(new Edge(to, weight));
        }

        public int[] dijkstra(int source) {
            int[] dist = new int[vertices];
            Arrays.fill(dist, Integer.MAX_VALUE);
            dist[source] = 0;

            boolean[] visited = new boolean[vertices];
            PriorityQueue<int[]> pq = new PriorityQueue<>(Comparator.comparingInt(a -> a[1]));
            pq.offer(new int[]{source, 0});

            while (!pq.isEmpty()) {
                int[] curr = pq.poll();
                int u = curr[0];

                if (visited[u]) {
                    continue;
                }
                visited[u] = true;

                List<Edge> neighbors = edges.get(u);
                if (neighbors != null) {
                    for (Edge edge : neighbors) {
                        if (visited[edge.to]) {
                            continue;
                        }
                        int newDist = dist[u] + edge.weight;
                        if (newDist < dist[edge.to]) {
                            dist[edge.to] = newDist;
                            pq.offer(new int[]{edge.to, newDist});
                        }
                    }
                }
            }

            return dist;
        }

        public List<Integer> bfs(int start) {
            Set<Integer> visited = new HashSet<>();
            Queue<Integer> queue = new LinkedList<>();
            List<Integer> result = new ArrayList<>();

            queue.offer(start);

            while (!queue.isEmpty()) {
                int u = queue.poll();
                if (visited.contains(u)) {
                    continue;
                }
                visited.add(u);
                result.add(u);

                List<Edge> neighbors = edges.get(u);
                if (neighbors != null) {
                    for (Edge edge : neighbors) {
                        if (!visited.contains(edge.to)) {
                            queue.offer(edge.to);
                        }
                    }
                }
            }

            return result;
        }

        public List<Integer> dfs(int start) {
            Set<Integer> visited = new HashSet<>();
            List<Integer> result = new ArrayList<>();
            dfsHelper(start, visited, result);
            return result;
        }

        private void dfsHelper(int u, Set<Integer> visited, List<Integer> result) {
            if (visited.contains(u)) {
                return;
            }
            visited.add(u);
            result.add(u);

            List<Edge> neighbors = edges.get(u);
            if (neighbors != null) {
                for (Edge edge : neighbors) {
                    dfsHelper(edge.to, visited, result);
                }
            }
        }
    }

    // ===== SORTING =====

    public static void quickSort(int[] arr) {
        if (arr == null || arr.length <= 1) {
            return;
        }
        quickSortHelper(arr, 0, arr.length - 1);
    }

    private static void quickSortHelper(int[] arr, int low, int high) {
        if (low < high) {
            int p = partition(arr, low, high);
            quickSortHelper(arr, low, p - 1);
            quickSortHelper(arr, p + 1, high);
        }
    }

    private static int partition(int[] arr, int low, int high) {
        int pivot = arr[high];
        int i = low - 1;

        for (int j = low; j < high; j++) {
            if (arr[j] < pivot) {
                i++;
                int temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }

        int temp = arr[i + 1];
        arr[i + 1] = arr[high];
        arr[high] = temp;
        return i + 1;
    }

    public static int[] mergeSort(int[] arr) {
        if (arr == null || arr.length <= 1) {
            return arr;
        }

        int mid = arr.length / 2;
        int[] left = mergeSort(Arrays.copyOfRange(arr, 0, mid));
        int[] right = mergeSort(Arrays.copyOfRange(arr, mid, arr.length));

        return merge(left, right);
    }

    private static int[] merge(int[] left, int[] right) {
        int[] result = new int[left.length + right.length];
        int i = 0, j = 0, k = 0;

        while (i < left.length && j < right.length) {
            if (left[i] <= right[j]) {
                result[k++] = left[i++];
            } else {
                result[k++] = right[j++];
            }
        }

        while (i < left.length) {
            result[k++] = left[i++];
        }
        while (j < right.length) {
            result[k++] = right[j++];
        }

        return result;
    }

    // ===== DYNAMIC PROGRAMMING =====

    public static String lcs(String s1, String s2) {
        int m = s1.length();
        int n = s2.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (s1.charAt(i - 1) == s2.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }

        // Backtrack
        StringBuilder result = new StringBuilder();
        int i = m, j = n;
        while (i > 0 && j > 0) {
            if (s1.charAt(i - 1) == s2.charAt(j - 1)) {
                result.insert(0, s1.charAt(i - 1));
                i--;
                j--;
            } else if (dp[i - 1][j] > dp[i][j - 1]) {
                i--;
            } else {
                j--;
            }
        }

        return result.toString();
    }

    public static int editDistance(String s1, String s2) {
        int m = s1.length();
        int n = s2.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 0; i <= m; i++) {
            dp[i][0] = i;
        }
        for (int j = 0; j <= n; j++) {
            dp[0][j] = j;
        }

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (s1.charAt(i - 1) == s2.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1];
                } else {
                    dp[i][j] = 1 + Math.min(dp[i - 1][j],
                            Math.min(dp[i][j - 1], dp[i - 1][j - 1]));
                }
            }
        }

        return dp[m][n];
    }

    public static int knapsack(int[] weights, int[] values, int capacity) {
        int n = weights.length;
        int[][] dp = new int[n + 1][capacity + 1];

        for (int i = 1; i <= n; i++) {
            for (int w = 0; w <= capacity; w++) {
                if (weights[i - 1] <= w) {
                    dp[i][w] = Math.max(dp[i - 1][w],
                            dp[i - 1][w - weights[i - 1]] + values[i - 1]);
                } else {
                    dp[i][w] = dp[i - 1][w];
                }
            }
        }

        return dp[n][capacity];
    }
}

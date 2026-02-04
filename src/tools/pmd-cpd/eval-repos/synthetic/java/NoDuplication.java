/**
 * Java file with no code duplication - all methods are unique.
 */
package synthetic;

import java.util.*;

public class NoDuplication {

    public static long calculateFibonacci(int n) {
        if (n <= 1) return n;
        long a = 0, b = 1;
        for (int i = 2; i <= n; i++) {
            long temp = a + b;
            a = b;
            b = temp;
        }
        return b;
    }

    public static boolean isPrime(int num) {
        if (num < 2) return false;
        if (num == 2) return true;
        if (num % 2 == 0) return false;
        for (int i = 3; i <= Math.sqrt(num); i += 2) {
            if (num % i == 0) return false;
        }
        return true;
    }

    public static int binarySearch(int[] arr, int target) {
        int left = 0, right = arr.length - 1;
        while (left <= right) {
            int mid = (left + right) / 2;
            if (arr[mid] == target) return mid;
            if (arr[mid] < target) left = mid + 1;
            else right = mid - 1;
        }
        return -1;
    }

    public static int[] mergeSort(int[] arr) {
        if (arr.length <= 1) return arr;
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
        while (i < left.length) result[k++] = left[i++];
        while (j < right.length) result[k++] = right[j++];
        return result;
    }
}

class DataProcessor {
    private final double[] data;
    private boolean processed = false;

    public DataProcessor(double[] data) {
        this.data = data;
    }

    public double[] normalize() {
        if (data.length == 0) return new double[0];
        double min = Arrays.stream(data).min().orElse(0);
        double max = Arrays.stream(data).max().orElse(0);
        if (max == min) {
            double[] result = new double[data.length];
            Arrays.fill(result, 0.5);
            return result;
        }
        return Arrays.stream(data).map(x -> (x - min) / (max - min)).toArray();
    }

    public Map<String, Double> computeStatistics() {
        if (data.length == 0) {
            return Map.of("mean", 0.0, "median", 0.0, "std", 0.0);
        }
        int n = data.length;
        double mean = Arrays.stream(data).average().orElse(0);
        double[] sorted = Arrays.stream(data).sorted().toArray();
        double median = n % 2 != 0 ? sorted[n / 2] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2;
        double variance = Arrays.stream(data).map(x -> Math.pow(x - mean, 2)).sum() / n;
        return Map.of("mean", mean, "median", median, "std", Math.sqrt(variance));
    }
}

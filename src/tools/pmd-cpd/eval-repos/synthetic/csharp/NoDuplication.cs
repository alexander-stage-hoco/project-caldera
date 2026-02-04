/// <summary>
/// C# file with no code duplication - all methods are unique.
/// </summary>

using System;
using System.Collections.Generic;
using System.Linq;

namespace Synthetic.NoDuplication
{
    public static class MathOperations
    {
        public static long CalculateFibonacci(int n)
        {
            if (n <= 1) return n;
            long a = 0, b = 1;
            for (int i = 2; i <= n; i++)
            {
                long temp = a + b;
                a = b;
                b = temp;
            }
            return b;
        }

        public static bool IsPrime(int num)
        {
            if (num < 2) return false;
            if (num == 2) return true;
            if (num % 2 == 0) return false;
            for (int i = 3; i <= Math.Sqrt(num); i += 2)
            {
                if (num % i == 0) return false;
            }
            return true;
        }

        public static int BinarySearch(int[] arr, int target)
        {
            int left = 0, right = arr.Length - 1;
            while (left <= right)
            {
                int mid = (left + right) / 2;
                if (arr[mid] == target) return mid;
                if (arr[mid] < target) left = mid + 1;
                else right = mid - 1;
            }
            return -1;
        }
    }

    public class DataProcessor
    {
        private readonly double[] _data;
        private bool _processed = false;

        public DataProcessor(double[] data)
        {
            _data = data;
        }

        public double[] Normalize()
        {
            if (_data.Length == 0) return Array.Empty<double>();
            double min = _data.Min();
            double max = _data.Max();
            if (max == min) return _data.Select(_ => 0.5).ToArray();
            return _data.Select(x => (x - min) / (max - min)).ToArray();
        }

        public (double Mean, double Median, double Std) ComputeStatistics()
        {
            if (_data.Length == 0) return (0, 0, 0);
            int n = _data.Length;
            double mean = _data.Average();
            var sorted = _data.OrderBy(x => x).ToArray();
            double median = n % 2 != 0 ? sorted[n / 2] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2;
            double variance = _data.Sum(x => Math.Pow(x - mean, 2)) / n;
            return (mean, median, Math.Sqrt(variance));
        }
    }
}

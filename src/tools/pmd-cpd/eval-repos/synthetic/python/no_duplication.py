"""Python file with no code duplication - all functions are unique."""


def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number using iteration."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def is_prime(num: int) -> bool:
    """Check if a number is prime."""
    if num < 2:
        return False
    if num == 2:
        return True
    if num % 2 == 0:
        return False
    for i in range(3, int(num**0.5) + 1, 2):
        if num % i == 0:
            return False
    return True


def binary_search(arr: list[int], target: int) -> int:
    """Perform binary search on a sorted array."""
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


def merge_sort(arr: list[int]) -> list[int]:
    """Sort an array using merge sort algorithm."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(left: list[int], right: list[int]) -> list[int]:
    """Merge two sorted arrays into one sorted array."""
    result = []
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


class DataProcessor:
    """A class for processing various types of data."""

    def __init__(self, data: list):
        self.data = data
        self.processed = False

    def normalize(self) -> list[float]:
        """Normalize numeric data to 0-1 range."""
        if not self.data:
            return []
        min_val = min(self.data)
        max_val = max(self.data)
        if max_val == min_val:
            return [0.5] * len(self.data)
        return [(x - min_val) / (max_val - min_val) for x in self.data]

    def compute_statistics(self) -> dict:
        """Compute basic statistics on the data."""
        if not self.data:
            return {"mean": 0, "median": 0, "std": 0}
        n = len(self.data)
        mean = sum(self.data) / n
        sorted_data = sorted(self.data)
        median = sorted_data[n // 2] if n % 2 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
        variance = sum((x - mean) ** 2 for x in self.data) / n
        return {"mean": mean, "median": median, "std": variance**0.5}

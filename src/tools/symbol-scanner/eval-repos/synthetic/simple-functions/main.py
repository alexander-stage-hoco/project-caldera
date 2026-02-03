"""Simple functions test repo - basic function definitions and calls."""


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


def process(data: list, verbose: bool = False) -> int:
    """Process data and return count."""
    result = len(data)
    if verbose:
        print(f"Processed {result} items")
    return result


def main():
    """Entry point."""
    message = greet("World")
    print(message)
    count = process([1, 2, 3], verbose=True)
    print(f"Count: {count}")


if __name__ == "__main__":
    main()

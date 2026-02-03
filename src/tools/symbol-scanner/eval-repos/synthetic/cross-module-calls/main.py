"""Main module for cross-module calls test."""

from processor import process_input, batch_process
from utils import format_output


def run():
    """Run the main process."""
    # Single item processing
    result = process_input("  Hello World  ")
    if result:
        output = format_output({"result": result})
        print(output)

    # Batch processing
    items = ["  Item 1  ", "  ", "  Item 2  "]
    processed = batch_process(items)
    print(f"Processed {len(processed)} items")


if __name__ == "__main__":
    run()

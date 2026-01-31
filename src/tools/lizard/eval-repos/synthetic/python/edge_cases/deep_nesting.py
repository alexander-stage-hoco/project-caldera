"""Deep nesting test - 10+ levels of indentation."""

def deeply_nested_function(data: dict) -> str:
    """Function with extreme nesting depth."""
    result = ""

    if data:  # Level 1
        if "level1" in data:  # Level 2
            for item in data["level1"]:  # Level 3
                if isinstance(item, dict):  # Level 4
                    for key, value in item.items():  # Level 5
                        if value:  # Level 6
                            try:  # Level 7
                                if isinstance(value, list):  # Level 8
                                    for v in value:  # Level 9
                                        if v > 0:  # Level 10
                                            while v > 0:  # Level 11
                                                if v % 2 == 0:  # Level 12
                                                    result += str(v)
                                                v -= 1
                            except Exception:
                                pass

    return result


class DeeplyNestedClass:
    """Class demonstrating deep nesting in methods."""

    def process(self, matrix: list) -> int:
        """Process a nested matrix structure."""
        total = 0

        if matrix:  # 1
            for row in matrix:  # 2
                if row:  # 3
                    for cell in row:  # 4
                        if isinstance(cell, dict):  # 5
                            for k, v in cell.items():  # 6
                                if v is not None:  # 7
                                    match v:  # 8
                                        case int():
                                            if v > 0:  # 9
                                                for i in range(v):  # 10
                                                    if i % 2:  # 11
                                                        total += i
                                        case _:
                                            pass

        return total

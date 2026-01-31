# -*- coding: utf-8 -*-
"""Unicode content test file."""

# Unicode variable names
变量 = "Chinese variable"
переменная = "Russian variable"
متغير = "Arabic variable"

# Unicode in strings
greeting = "Hello, 世界! 🌍"
emoji_math = "1️⃣ + 2️⃣ = 3️⃣"

# Unicode function name
def 计算(数值: int) -> int:
    """Calculate double of a number."""
    return 数值 * 2

# Unicode class
class Größe:
    """Size class with German umlaut."""

    def __init__(self, wert: float):
        self.größe = wert

    def получить(self) -> float:
        """Get value (Russian method name)."""
        return self.größe

# Test
результат = 计算(5)
objekt = Größe(3.14)

"""Deep nesting stress test - 10+ levels of nested structures."""

from __future__ import annotations


class Level1:
    """First level of nesting."""

    class Level2:
        """Second level of nesting."""

        class Level3:
            """Third level of nesting."""

            class Level4:
                """Fourth level of nesting."""

                class Level5:
                    """Fifth level of nesting."""

                    class Level6:
                        """Sixth level of nesting."""

                        class Level7:
                            """Seventh level of nesting."""

                            class Level8:
                                """Eighth level of nesting."""

                                class Level9:
                                    """Ninth level of nesting."""

                                    class Level10:
                                        """Tenth level - deepest class nesting."""

                                        def deepest_method(self) -> str:
                                            """Method at the deepest level."""
                                            return "deepest"

                                    def level9_method(self) -> int:
                                        """Method at level 9."""
                                        return 9

                                def level8_method(self) -> int:
                                    """Method at level 8."""
                                    return 8

                            def level7_method(self) -> int:
                                """Method at level 7."""
                                return 7

                        def level6_method(self) -> int:
                            """Method at level 6."""
                            return 6

                    def level5_method(self) -> int:
                        """Method at level 5."""
                        return 5

                def level4_method(self) -> int:
                    """Method at level 4."""
                    return 4

            def level3_method(self) -> int:
                """Method at level 3."""
                return 3

        def level2_method(self) -> int:
            """Method at level 2."""
            return 2

    def level1_method(self) -> int:
        """Method at level 1."""
        return 1


def outer_function():
    """Outer function with nested functions."""

    def nested_1():
        """First nested function."""

        def nested_2():
            """Second nested function."""

            def nested_3():
                """Third nested function."""

                def nested_4():
                    """Fourth nested function."""

                    def nested_5():
                        """Fifth nested function - deepest function nesting."""
                        return "nested_5"

                    return nested_5()

                return nested_4()

            return nested_3()

        return nested_2()

    return nested_1()


def _private_deeply_nested():
    """Private function with deep nesting (reduced weight)."""

    def _inner():
        def _deeper():
            return "deep"
        return _deeper()

    return _inner()


if __name__ == "__main__":
    # Access deepest class
    obj = Level1.Level2.Level3.Level4.Level5.Level6.Level7.Level8.Level9.Level10()
    print(obj.deepest_method())

    # Call deeply nested function
    print(outer_function())

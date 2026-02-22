from src.main import greet


def test_greet():
    assert greet("CI") == "Hello, CI!"

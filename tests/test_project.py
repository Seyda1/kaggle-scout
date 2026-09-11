"""Smoke tests for project setup."""


def test_package_imports() -> None:
    import kaggle_scout

    assert kaggle_scout.__name__ == "kaggle_scout"
    assert kaggle_scout.__version__ == "0.1.0"

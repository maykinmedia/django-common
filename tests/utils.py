import importlib.util


def is_dependency_installed(*dependencies: str) -> bool:
    """
    Test if any of the specified dependencies are installed.
    """
    check_generator = (
        importlib.util.find_spec(dependency) is not None for dependency in dependencies
    )
    return any(check_generator)

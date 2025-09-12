from pathlib import Path


def find_pyproject_dir(curr_path: Path, nth: int = 1) -> Path:
    """Find the directory that contains the pyproject.toml file."""
    if curr_path.is_file():
        curr_path = curr_path.parent

    n_found = 0
    while True:
        if (curr_path / 'pyproject.toml').exists():
            n_found += 1
            if n_found == nth:
                return curr_path
        elif curr_path.parent == curr_path:
            raise FileNotFoundError
        curr_path = curr_path.parent

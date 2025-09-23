from pathlib import Path

from rich.console import Console, RenderableType
from rich.text import Text


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


def get_rich_str(
    *renderables: RenderableType | object, plain: bool = True
) -> str:
    console = Console(
        record=True,
        width=80,
        color_system='standard',
        force_terminal=False,
        force_interactive=False,
        force_jupyter=False,
    )
    with console.capture() as capture:
        for renderable in renderables:
            console.print(renderable)
    exported_text = capture.get()
    if plain:
        return Text.from_ansi(exported_text).plain
    else:
        return exported_text

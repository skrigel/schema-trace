# main.py
import typer
from rich.console import Console

app = typer.Typer(help="A simple CLI tool example.")
console = Console()

@app.command()
def hello(name: str, formal: bool = typer.Option(False, "--formal", "-f", help="Say hello formally.")):
    """
    Say hello to a given name.
    """
    if formal:
        console.print(f"Hello, [bold]{name}[/bold] sir/ma'am!")
    else:
        console.print(f"Hello, {name}!")

if __name__ == "__main__":
    app()

# app.py
"""
Railpack entry point that imports and runs the web interface from cli.py
"""
from cli import cli

if __name__ == "__main__":
    # This will be used by Railpack to start the web server
    cli(prog_name="python_terminal")

#!/usr/bin/env python3
"""
CLI launcher for the Python Terminal
"""

import os
import subprocess
import sys

import click

from terminal import EnhancedTerminal as Terminal


@click.group()
def cli():
    """Python Terminal - A fully functioning command terminal built in Python."""
    pass

@cli.command()
def start():
    """Start the interactive terminal (CLI mode)."""
    terminal = Terminal()
    terminal.run()

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind the web server to')
@click.option('--port', default=5000, help='Port to bind the web server to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def web(host, port, debug):
    """Start the web-based terminal interface."""
    try:
        from web_terminal import app
        print(f"🌐 Starting web terminal at http://{host}:{port}")
        print("Press Ctrl+C to stop the server")
        app.run(host=host, port=port, debug=debug)
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Make sure Flask is installed: pip install flask")
        sys.exit(1)

@cli.command()
@click.argument('command', nargs=-1)
def exec(command):
    """Execute a single command and exit."""
    if not command:
        print("No command provided")
        sys.exit(1)
    
    terminal = Terminal()
    output, exit_code = terminal.execute_command(' '.join(command))
    
    if output:
        print(output)
    
    sys.exit(exit_code)

@cli.command()
def install():
    """Install required dependencies."""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)

@cli.command()
def test():
    """Run basic functionality tests."""
    print("🧪 Running terminal tests...")
    
    terminal = Terminal()
    test_commands = [
        'pwd',
        'whoami',
        'date',
        'ls',
        'help'
    ]
    
    passed = 0
    total = len(test_commands)
    
    for cmd in test_commands:
        try:
            output, exit_code = terminal.execute_command(cmd)
            if exit_code == 0:
                print(f"✅ {cmd}")
                passed += 1
            else:
                print(f"❌ {cmd} (exit code: {exit_code})")
        except Exception as e:
            print(f"❌ {cmd} (error: {e})")
    
    print(f"\n📊 Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
        sys.exit(1)

if __name__ == '__main__':
    cli()

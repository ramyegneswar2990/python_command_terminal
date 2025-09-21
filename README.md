# Python Command Terminal

A powerful, extensible command-line terminal built with Python, featuring AI-powered command interpretation and a web interface.

![Terminal Demo](https://img.shields.io/badge/demo-available-green.svg)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

- **Interactive Command-Line Interface** with syntax highlighting and command history
- **Web-Based Terminal** accessible through a browser
- **AI-Powered Commands** using Google's Gemini AI (API key required)
- **Cross-Platform** - Works on Windows, macOS, and Linux
- **Familiar Commands** with enhanced functionality:
  - File operations (ls, cd, cp, mv, rm, etc.)
  - Process management (ps, top, kill)
  - System monitoring (df, du, free, uptime)
  - And many more!

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ramyegneswar2990/python_command_terminal.git
   cd python_command_terminal
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

#### Command-Line Interface
```bash
# Start the interactive terminal
python -m python_terminal.cli start

# Execute a single command
python -m python_terminal.cli exec "ls -la"
```

#### Web Interface
```bash
# Start the web server (default: http://127.0.0.1:5000/)
python -m python_terminal.cli web
```

#### AI-Powered Commands
Enable AI features by setting the `GEMINI_API_KEY` environment variable:
```bash
# On Windows
set GEMINI_API_KEY=your_api_key_here

# On Unix/Linux/macOS
export GEMINI_API_KEY=your_api_key_here

# Then start the terminal
python -m python_terminal.cli start
```

In the terminal, use the `ai` command to get AI-powered command suggestions:
```
$ ai list all files modified in the last 7 days
```

## 📚 Available Commands

### File Operations
- `ls` - List directory contents
- `cd` - Change directory
- `cp` - Copy files/directories
- `mv` - Move/rename files/directories
- `rm` - Remove files
- `mkdir` - Create directories
- `cat` - Display file contents
- `find` - Search for files

### System Information
- `ps` - List processes
- `top` - Display processes
- `df` - Disk space usage
- `du` - Directory space usage
- `free` - Memory usage
- `uptime` - System uptime
- `whoami` - Current user

### AI Commands
- `ai <query>` - Get AI-powered command suggestions
- `smart <natural language command>` - Execute natural language commands

## 🌐 Web Interface

The web interface provides a modern, browser-based terminal experience:
- Responsive design that works on desktop and mobile
- Command history
- AI command suggestions
- Real-time output

## 🤖 AI Integration

This terminal integrates with Google's Gemini AI to provide intelligent command suggestions and natural language processing. To use AI features:

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/)
2. Set it as an environment variable `GEMINI_API_KEY`
3. Start the terminal with AI features enabled

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python and Flask
- Uses Google's Gemini AI for natural language processing
- Inspired by traditional Unix shells and modern terminal emulators
<img width="1915" height="878" alt="image" src="https://github.com/user-attachments/assets/e7f001ee-7aa2-45f9-9610-cadb5b2d56bf" />

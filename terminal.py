#!/usr/bin/env python3
"""
Enhanced Python-Based Command Terminal with Gemini AI Integration
A fully functioning command terminal with AI-powered natural language processing.
"""

import glob
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import psutil
import requests
from colorama import Back, Fore, Style, init
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import PathCompleter, WordCompleter
from prompt_toolkit.history import InMemoryHistory

# Initialize colorama for cross-platform colored output
init(autoreset=True)



def expand_wildcards(command: str) -> str:
    """Expand wildcards like * or *.txt on Windows before execution."""
    if platform.system() == "Windows":
        parts = shlex.split(command, posix=False)
        expanded = []
        for part in parts:
            if '*' in part or '?' in part:
                matches = glob.glob(part)
                if matches:
                    expanded.extend(matches)
                else:
                    expanded.append(part)
            else:
                expanded.append(part)
        # Join back for subprocess
        return " ".join(shlex.quote(p) for p in expanded)
    else:
        return command  # Linux/macOS handles wildcards natively

class GeminiAI:
    """Google Gemini AI integration for natural language command interpretation."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def interpret_command(self, natural_language: str, current_dir: str, available_files: List[str]) -> Dict[str, Any]:
        """Interpret natural language into terminal commands."""

        system_prompt = (
            "You are an expert terminal command interpreter. Convert natural language requests into appropriate "
            "terminal commands.\n\n"
            "Rules:\n"
            "1. For file operations, use exact file names from the available files list when possible\n"
            "2. For directory operations, suggest appropriate directory names\n"
            "3. Use standard Unix/Linux commands (ls, cd, mkdir, rm, cp, mv, cat, grep, etc.)\n"
            "4. If the request is unclear or impossible, set success to false\n"
            "5. Break complex operations into multiple commands\n"
            "6. Always prioritize safety - avoid destructive operations without clear intent\n\n"
            "Respond with a JSON object containing:\n"
            "{\n"
            "  \"commands\": [\"command1\", \"command2\", ...],\n"
            "  \"explanation\": \"Brief explanation\",\n"
            "  \"success\": true/false,\n"
            "  \"error_message\": \"Error message if success is false\"\n"
            "}"
        )

        user_prompt = (
            f"Context:\n"
            f"- Current directory: {current_dir}\n"
            f"- Available files/folders: {', '.join(available_files[:20])}\n"
            f"- Operating system: {platform.system()}\n\n"
            f"Natural language request: \"{natural_language}\""
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        }

        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                # Clean JSON if wrapped in markdown
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]

                try:
                    return json.loads(content.strip())
                except json.JSONDecodeError:
                    return {
                        "commands": [],
                        "explanation": f"AI response parsing error. Raw response: {content[:200]}...",
                        "success": False,
                        "error_message": "Failed to parse AI response"
                    }
            else:
                return {
                    "commands": [],
                    "explanation": f"AI API error: {response.status_code}",
                    "success": False,
                    "error_message": f"API request failed with status {response.status_code}: {response.text}"
                }

        except requests.exceptions.RequestException as e:
            return {
                "commands": [],
                "explanation": f"Network error: {str(e)}",
                "success": False,
                "error_message": f"Failed to connect to Gemini AI: {str(e)}"
            }
        except Exception as e:
            return {
                "commands": [],
                "explanation": f"Unexpected error: {str(e)}",
                "success": False,
                "error_message": f"Unexpected error occurred: {str(e)}"
            }


class EnhancedTerminal:
    """Enhanced terminal class with Gemini AI integration."""
    
    def __init__(self, gemini_api_key: str = None):
        self.current_dir = os.getcwd()
        self.history = InMemoryHistory()
        self.session = PromptSession(history=self.history)
        self.command_history = []
        self.aliases = {
            'll': 'ls -la',
            'la': 'ls -la',
            '..': 'cd ..',
            '...': 'cd ../..',
            'h': 'history',
            'c': 'clear',
            'q': 'exit'
        }
        
        # Initialize Gemini AI if API key is provided
        self.gemini_ai = GeminiAI(gemini_api_key) if gemini_api_key else None
        
        # Command completers
        self.path_completer = PathCompleter()
        self.command_completer = WordCompleter([
            'ls', 'cd', 'pwd', 'mkdir', 'rm', 'rmdir', 'cp', 'mv', 'cat', 'echo',
            'grep', 'find', 'ps', 'top', 'kill', 'df', 'du', 'free', 'uptime',
            'whoami', 'date', 'history', 'clear', 'exit', 'help', 'ai', 'smart'
        ])
        
    def display_prompt(self) -> str:
        """Generate the terminal prompt with current directory and user info."""
        try:
            username = os.getenv('USERNAME', 'user')
            hostname = platform.node()
            cwd = os.path.basename(self.current_dir) or self.current_dir
            if len(cwd) > 20:
                cwd = cwd[:17] + "..."
            
            # Add AI indicator if available
            ai_indicator = f"{Fore.MAGENTA}[AI]{Style.RESET_ALL}" if self.gemini_ai else ""
            
            return f"{ai_indicator}{Fore.GREEN}{username}@{hostname}{Fore.WHITE}:{Fore.BLUE}{cwd}{Fore.WHITE}$ "
        except:
            return f"{Fore.GREEN}user@terminal{Fore.WHITE}:{Fore.BLUE}{os.path.basename(self.current_dir)}{Fore.WHITE}$ "
    
    def get_available_files(self) -> List[str]:
        """Get list of files and directories in current directory."""
        try:
            return os.listdir(self.current_dir)
        except PermissionError:
            return []
        except Exception:
            return []
    
    def execute_command(self, command: str) -> Tuple[str, int]:
        """Execute a command and return output and exit code."""
        if not command.strip():
            return "", 0
            
        # Add to history
        self.command_history.append(command)
        
        # Handle aliases
        command = self._expand_aliases(command)
        
        # Split command into parts
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            # Built-in commands
            if cmd in ['exit', 'quit']:
                return "Goodbye!", 0
            elif cmd == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                return "", 0
            elif cmd == 'pwd':
                return self.current_dir, 0
            elif cmd == 'cd':
                return self._handle_cd(args)
            elif cmd == 'ls':
                return self._handle_ls(args)
            elif cmd == 'mkdir':
                return self._handle_mkdir(args)
            elif cmd == 'rm':
                return self._handle_rm(args)
            elif cmd == 'rmdir':
                return self._handle_rmdir(args)
            elif cmd == 'cp':
                return self._handle_cp(args)
            elif cmd == 'mv':
                return self._handle_mv(args)
            elif cmd == 'cat':
                return self._handle_cat(args)
            elif cmd == 'echo':
                return self._handle_echo(args)
            elif cmd == 'grep':
                return self._handle_grep(args)
            elif cmd == 'find':
                return self._handle_find(args)
            elif cmd == 'ps':
                return self._handle_ps(args)
            elif cmd == 'top':
                return self._handle_top(args)
            elif cmd == 'kill':
                return self._handle_kill(args)
            elif cmd == 'df':
                return self._handle_df(args)
            elif cmd == 'du':
                return self._handle_du(args)
            elif cmd == 'free':
                return self._handle_free(args)
            elif cmd == 'uptime':
                return self._handle_uptime(args)
            elif cmd == 'whoami':
                return self._handle_whoami(args)
            elif cmd == 'date':
                return self._handle_date(args)
            elif cmd == 'history':
                return self._handle_history(args)
            elif cmd == 'help':
                return self._handle_help(args)
            elif cmd in ['ai', 'smart']:
                return self._handle_ai_command(args)
            elif cmd == 'touch':
                return self._handle_touch(args)
            else:
                # Try to execute as system command
                return self._execute_system_command(command)
                
        except Exception as e:
            return f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}", 1
    
    def _expand_aliases(self, command: str) -> str:
        """Expand command aliases."""
        parts = command.split()
        if parts and parts[0] in self.aliases:
            return command.replace(parts[0], self.aliases[parts[0]], 1)
        return command
    
    def _handle_ai_command(self, args: List[str]) -> Tuple[str, int]:
        """Handle AI-powered command interpretation."""
        if not self.gemini_ai:
            return f"{Fore.RED}AI functionality not available. Please provide a Gemini API key.{Style.RESET_ALL}", 1
        
        if not args:
            return f"{Fore.YELLOW}Usage: ai <natural language command>\nExample: ai show me all python files{Style.RESET_ALL}", 1
        
        natural_language = ' '.join(args)
        
        print(f"{Fore.CYAN}🤖 Processing with AI: {natural_language}{Style.RESET_ALL}")
        
        # Get context
        available_files = self.get_available_files()
        
        # Use Gemini AI to interpret the command
        ai_response = self.gemini_ai.interpret_command(natural_language, self.current_dir, available_files)
        
        if not ai_response.get('success', False):
            return f"{Fore.RED}AI Error: {ai_response.get('error_message', 'Unknown error')}{Style.RESET_ALL}", 1
        
        commands = ai_response.get('commands', [])
        explanation = ai_response.get('explanation', '')
        
        if not commands:
            return f"{Fore.YELLOW}AI could not interpret the request: {explanation}{Style.RESET_ALL}", 1
        
        print(f"{Fore.GREEN}💡 AI Interpretation: {explanation}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📝 Commands to execute: {' && '.join(commands)}{Style.RESET_ALL}")
        
        # Ask for confirmation for potentially destructive operations
        destructive_commands = ['rm', 'rmdir', 'mv', 'kill']
        if any(any(dest_cmd in cmd for dest_cmd in destructive_commands) for cmd in commands):
            try:
                confirm = input(f"{Fore.YELLOW}⚠️  This operation may modify/delete files. Continue? (y/n): {Style.RESET_ALL}")
                if confirm.lower() not in ['y', 'yes']:
                    return f"{Fore.YELLOW}Operation cancelled by user.{Style.RESET_ALL}", 0
            except KeyboardInterrupt:
                return f"{Fore.YELLOW}Operation cancelled by user.{Style.RESET_ALL}", 0
        
        # Execute commands sequentially
        results = []
        overall_exit_code = 0
        
        for i, cmd in enumerate(commands, 1):
            print(f"{Fore.CYAN}[{i}/{len(commands)}] Executing: {cmd}{Style.RESET_ALL}")
            output, exit_code = self.execute_command(cmd)
            
            if output.strip():
                results.append(output)
            
            if exit_code != 0:
                overall_exit_code = exit_code
                results.append(f"{Fore.RED}Command failed with exit code {exit_code}{Style.RESET_ALL}")
                break  # Stop on first failure
        
        final_output = '\n'.join(results) if results else f"{Fore.GREEN}✅ All commands executed successfully!{Style.RESET_ALL}"
        return final_output, overall_exit_code
    
    # ... [Include all the original handler methods from the original Terminal class] ...
    
    def _handle_cd(self, args: List[str]) -> Tuple[str, int]:
        """Handle cd command."""
        if not args:
            new_dir = os.path.expanduser("~")
        else:
            new_dir = args[0]
        
        if new_dir.startswith('~'):
            new_dir = os.path.expanduser(new_dir)
        elif not os.path.isabs(new_dir):
            new_dir = os.path.join(self.current_dir, new_dir)
        
        try:
            os.chdir(new_dir)
            self.current_dir = os.getcwd()
            return "", 0
        except FileNotFoundError:
            return f"{Fore.RED}cd: {new_dir}: No such file or directory{Style.RESET_ALL}", 1
        except PermissionError:
            return f"{Fore.RED}cd: {new_dir}: Permission denied{Style.RESET_ALL}", 1
    
    def _handle_ls(self, args: List[str]) -> Tuple[str, int]:
        """Handle ls command."""
        path = self.current_dir
        show_hidden = False
        long_format = False
        
        for arg in args:
            if arg.startswith('-'):
                if 'a' in arg:
                    show_hidden = True
                if 'l' in arg:
                    long_format = True
            elif not arg.startswith('-'):
                path = arg
        
        try:
            if not os.path.exists(path):
                return f"{Fore.RED}ls: {path}: No such file or directory{Style.RESET_ALL}", 1
            
            if os.path.isfile(path):
                return path, 0
            
            items = os.listdir(path)
            if not show_hidden:
                items = [item for item in items if not item.startswith('.')]
            
            items.sort()
            
            if long_format:
                result = []
                for item in items:
                    item_path = os.path.join(path, item)
                    try:
                        stat = os.stat(item_path)
                        size = stat.st_size
                        mtime = time.strftime('%b %d %H:%M', time.localtime(stat.st_mtime))
                        if os.path.isdir(item_path):
                            result.append(f"drwxr-xr-x 1 user user {size:>8} {mtime} {Fore.BLUE}{item}{Style.RESET_ALL}")
                        else:
                            result.append(f"-rw-r--r-- 1 user user {size:>8} {mtime} {item}")
                    except:
                        result.append(f"?rwx------ 1 user user        0 Jan  1 00:00 {item}")
                return '\n'.join(result), 0
            else:
                colored_items = []
                for item in items:
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        colored_items.append(f"{Fore.BLUE}{item}{Style.RESET_ALL}")
                    else:
                        colored_items.append(item)
                return '  '.join(colored_items), 0
                
        except PermissionError:
            return f"{Fore.RED}ls: {path}: Permission denied{Style.RESET_ALL}", 1
        
    def handle_check_memory(self) -> Tuple[str, int]:
        """Return memory usage in a cross-platform way."""
        import psutil

        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        result = [
            f"Total Memory: {memory.total / (1024 ** 2):.2f} MB",
            f"Used Memory: {memory.used / (1024 ** 2):.2f} MB",
            f"Available Memory: {memory.available / (1024 ** 2):.2f} MB",
            f"Memory Usage: {memory.percent}%",
            f"Total Swap: {swap.total / (1024 ** 2):.2f} MB",
            f"Used Swap: {swap.used / (1024 ** 2):.2f} MB",
            f"Free Swap: {swap.free / (1024 ** 2):.2f} MB",
            f"Swap Usage: {swap.percent}%"
        ]
        return "\n".join(result), 0

    
    def _handle_mkdir(self, args: List[str]) -> Tuple[str, int]:
        """Handle mkdir command with multiple directories and wildcard expansion."""
        if not args:
            return f"{Fore.RED}mkdir: missing operand{Style.RESET_ALL}", 1

        for pattern in args:
            matched_dirs = glob.glob(os.path.join(self.current_dir, pattern)) if '*' in pattern or '?' in pattern else [pattern]

            # If wildcard did not match, create new directory
            if not matched_dirs or '*' in pattern or '?' in pattern:
                matched_dirs = [pattern]

            for dir_name in matched_dirs:
                try:
                    os.makedirs(dir_name, exist_ok=True)
                except PermissionError:
                    return f"{Fore.RED}mkdir: {dir_name}: Permission denied{Style.RESET_ALL}", 1
                except Exception as e:
                    return f"{Fore.RED}mkdir: {dir_name}: {str(e)}{Style.RESET_ALL}", 1

        return "", 0

    
    def _handle_rm(self, args: List[str]) -> Tuple[str, int]:
        """Handle rm command with wildcard support."""
        if not args:
            return f"{Fore.RED}rm: missing operand{Style.RESET_ALL}", 1

        recursive = False
        files_to_remove = []

        for arg in args:
            if arg in ['-r', '-rf']:
                recursive = True
            else:
                # Expand wildcard
                matched = glob.glob(os.path.join(self.current_dir, arg)) if '*' in arg or '?' in arg else [arg]
                files_to_remove.extend(matched)

        if not files_to_remove:
            return f"{Fore.RED}rm: no files matched{Style.RESET_ALL}", 1

        for file_path in files_to_remove:
            try:
                if os.path.isdir(file_path) and not recursive:
                    return f"{Fore.RED}rm: {file_path}: is a directory (use -r to remove){Style.RESET_ALL}", 1
                elif os.path.isdir(file_path) and recursive:
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            except FileNotFoundError:
                return f"{Fore.RED}rm: {file_path}: No such file or directory{Style.RESET_ALL}", 1
            except PermissionError:
                return f"{Fore.RED}rm: {file_path}: Permission denied{Style.RESET_ALL}", 1

        return "", 0

    
    def _handle_rmdir(self, args: List[str]) -> Tuple[str, int]:
        """Handle rmdir command."""
        if not args:
            return f"{Fore.RED}rmdir: missing operand{Style.RESET_ALL}", 1
        
        for dir_name in args:
            try:
                os.rmdir(dir_name)
            except FileNotFoundError:
                return f"{Fore.RED}rmdir: {dir_name}: No such file or directory{Style.RESET_ALL}", 1
            except OSError as e:
                return f"{Fore.RED}rmdir: {dir_name}: {str(e)}{Style.RESET_ALL}", 1
        
        return "", 0
    
    def _handle_cp(self, args: List[str]) -> Tuple[str, int]:
        """Handle cp command with wildcard support."""
        if len(args) < 2:
            return f"{Fore.RED}cp: missing file operand{Style.RESET_ALL}", 1
        
        src_pattern = args[0]
        dst = args[1]

        # Expand wildcard
        if '*' in src_pattern or '?' in src_pattern:
            matched_files = glob.glob(os.path.join(self.current_dir, src_pattern))
            if not matched_files:
                return f"{Fore.RED}cp: {src_pattern}: No files matched{Style.RESET_ALL}", 1
        else:
            matched_files = [src_pattern]

        try:
            for src in matched_files:
                if os.path.isdir(dst):
                    final_dst = os.path.join(dst, os.path.basename(src))
                else:
                    final_dst = dst
                shutil.copy2(src, final_dst)
        except FileNotFoundError:
            return f"{Fore.RED}cp: {src}: No such file or directory{Style.RESET_ALL}", 1
        except PermissionError:
            return f"{Fore.RED}cp: {src}: Permission denied{Style.RESET_ALL}", 1

        return "", 0

    
    def _handle_mv(self, args: List[str]) -> Tuple[str, int]:
        """Handle mv command with wildcard support."""
        if len(args) < 2:
            return f"{Fore.RED}mv: missing file operand{Style.RESET_ALL}", 1

        src_pattern = args[0]
        dst = args[1]

        matched_files = glob.glob(os.path.join(self.current_dir, src_pattern)) if '*' in src_pattern or '?' in src_pattern else [src_pattern]
        if not matched_files:
            return f"{Fore.RED}mv: {src_pattern}: No files matched{Style.RESET_ALL}", 1

        try:
            for src in matched_files:
                final_dst = dst
                if os.path.isdir(dst):
                    final_dst = os.path.join(dst, os.path.basename(src))
                shutil.move(src, final_dst)
        except FileNotFoundError:
            return f"{Fore.RED}mv: {src}: No such file or directory{Style.RESET_ALL}", 1
        except PermissionError:
            return f"{Fore.RED}mv: {src}: Permission denied{Style.RESET_ALL}", 1

        return "", 0

    
    def _handle_cat(self, args: List[str]) -> Tuple[str, int]:
        """Handle cat command."""
        if not args:
            return f"{Fore.RED}cat: missing operand{Style.RESET_ALL}", 1
        
        result = []
        for file_path in args:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    result.append(f.read())
            except FileNotFoundError:
                return f"{Fore.RED}cat: {file_path}: No such file or directory{Style.RESET_ALL}", 1
            except PermissionError:
                return f"{Fore.RED}cat: {file_path}: Permission denied{Style.RESET_ALL}", 1
        
        return '\n'.join(result), 0
    
    def _handle_echo(self, args: List[str]) -> Tuple[str, int]:
        """Handle echo command."""
        return ' '.join(args), 0
    
    def _handle_grep(self, args: List[str]) -> Tuple[str, int]:
        """Handle grep command."""
        if len(args) < 1:
            return f"{Fore.RED}grep: missing pattern{Style.RESET_ALL}", 1
        
        pattern = args[0]
        files = args[1:] if len(args) > 1 else []
        
        if not files:
            return f"{Fore.RED}grep: reading from stdin not implemented{Style.RESET_ALL}", 1
        
        result = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern in line:
                            result.append(f"{file_path}:{line_num}:{line.rstrip()}")
            except FileNotFoundError:
                result.append(f"{Fore.RED}grep: {file_path}: No such file or directory{Style.RESET_ALL}")
            except PermissionError:
                result.append(f"{Fore.RED}grep: {file_path}: Permission denied{Style.RESET_ALL}")
        
        return '\n'.join(result), 0
    
    def _handle_find(self, args: List[str]) -> Tuple[str, int]:
        """Handle find command."""
        if not args:
            return f"{Fore.RED}find: missing path{Style.RESET_ALL}", 1
        
        path = args[0]
        name_pattern = None
        
        if len(args) > 1 and args[1] == '-name':
            if len(args) > 2:
                name_pattern = args[2]
            else:
                return f"{Fore.RED}find: missing argument to -name{Style.RESET_ALL}", 1
        
        result = []
        try:
            for root, dirs, files in os.walk(path):
                for item in dirs + files:
                    item_path = os.path.join(root, item)
                    if name_pattern is None or name_pattern in item:
                        result.append(item_path)
        except PermissionError:
            return f"{Fore.RED}find: {path}: Permission denied{Style.RESET_ALL}", 1
        
        return '\n'.join(result), 0
    
    def _handle_ps(self, args: List[str]) -> Tuple[str, int]:
        """Handle ps command."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    processes.append(f"{pinfo['pid']:>6} {pinfo['name']:<20} {pinfo['cpu_percent']:>6.1f} {pinfo['memory_percent']:>6.1f}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            header = f"{'PID':>6} {'NAME':<20} {'CPU%':>6} {'MEM%':>6}"
            return f"{header}\n" + '\n'.join(processes), 0
        except Exception as e:
            return f"{Fore.RED}ps: {str(e)}{Style.RESET_ALL}", 1
    
    def _handle_top(self, args: List[str]) -> Tuple[str, int]:
        """Handle top command."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    memory_mb = pinfo['memory_info'].rss / 1024 / 1024
                    processes.append((pinfo['cpu_percent'], pinfo['pid'], pinfo['name'], memory_mb))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes.sort(reverse=True)
            
            result = ["PID    NAME                 CPU%   MEM(MB)"]
            for cpu, pid, name, mem in processes[:10]:
                result.append(f"{pid:>6} {name:<20} {cpu:>6.1f} {mem:>8.1f}")
            
            return '\n'.join(result), 0
        except Exception as e:
            return f"{Fore.RED}top: {str(e)}{Style.RESET_ALL}", 1
    
    def _handle_kill(self, args: List[str]) -> Tuple[str, int]:
        """Handle kill command."""
        if not args:
            return f"{Fore.RED}kill: missing operand{Style.RESET_ALL}", 1
        
        try:
            pid = int(args[0])
            proc = psutil.Process(pid)
            proc.terminate()
            return "", 0
        except ValueError:
            return f"{Fore.RED}kill: {args[0]}: invalid process ID{Style.RESET_ALL}", 1
        except psutil.NoSuchProcess:
            return f"{Fore.RED}kill: {args[0]}: No such process{Style.RESET_ALL}", 1
        except psutil.AccessDenied:
            return f"{Fore.RED}kill: {args[0]}: Permission denied{Style.RESET_ALL}", 1
    
    def _handle_df(self, args: List[str]) -> Tuple[str, int]:
        """Handle df command."""
        try:
            result = ["Filesystem     1K-blocks     Used Available Use% Mounted on"]
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total = usage.total // 1024
                    used = usage.used // 1024
                    available = usage.free // 1024
                    percent = (used / total) * 100 if total > 0 else 0
                    result.append(f"{partition.device:<15} {total:>8} {used:>8} {available:>8} {percent:>4.0f}% {partition.mountpoint}")
                except PermissionError:
                    pass
            return '\n'.join(result), 0
        except Exception as e:
            return f"{Fore.RED}df: {str(e)}{Style.RESET_ALL}", 1
    
    def _handle_du(self, args: List[str]) -> Tuple[str, int]:
        """Handle du command."""
        path = args[0] if args else "."
        
        try:
            total_size = 0
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        pass
            
            size_mb = total_size / (1024 * 1024)
            return f"{size_mb:.1f}M\t{path}", 0
        except Exception as e:
            return f"{Fore.RED}du: {str(e)}{Style.RESET_ALL}", 1
    
    def _handle_free(self, args: List[str]) -> Tuple[str, int]:
        """Handle free command."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            shared = getattr(memory, 'shared', 0)
            buffers = getattr(memory, 'buffers', 0)
            cached = getattr(memory, 'cached', 0)
            
            result = [
                "              total        used        free      shared  buff/cache   available",
                f"Mem:        {memory.total:>10} {memory.used:>10} {memory.available:>10} {shared:>10} {buffers + cached:>10} {memory.available:>10}",
                f"Swap:       {swap.total:>10} {swap.used:>10} {swap.free:>10} {0:>10} {0:>10} {swap.free:>10}"
            ]
            return '\n'.join(result), 0
        except Exception as e:
            return f"{Fore.RED}free: {str(e)}{Style.RESET_ALL}", 1
    
    def _handle_uptime(self, args: List[str]) -> Tuple[str, int]:
        """Handle uptime command."""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            
            return f"up {days} days, {hours:02d}:{minutes:02d}, load average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}", 0
        except Exception as e:
            return f"{Fore.RED}uptime: {str(e)}{Style.RESET_ALL}", 1
    
    def _handle_whoami(self, args: List[str]) -> Tuple[str, int]:
        """Handle whoami command."""
        return os.getenv('USERNAME', 'user'), 0
    
    def _handle_date(self, args: List[str]) -> Tuple[str, int]:
        """Handle date command."""
        return time.strftime('%a %b %d %H:%M:%S %Z %Y'), 0
    
    def _handle_history(self, args: List[str]) -> Tuple[str, int]:
        """Handle history command."""
        if not self.command_history:
            return "No commands in history", 0
        
        result = []
        for i, cmd in enumerate(self.command_history[-20:], 1):
            result.append(f"{i:>4}  {cmd}")
        
        return '\n'.join(result), 0
    
    def _handle_help(self, args: List[str]) -> Tuple[str, int]:
        """Handle help command."""
        ai_help = f"""
  AI Commands:
    ai <query>              - Execute natural language commands using Gemini AI
    smart <query>           - Same as ai command
    
  AI Examples:
    ai show me all python files
    ai create a backup folder and copy all text files to it
    ai find the largest files in this directory
    ai show me running processes using more than 50% CPU
    smart delete all files with .tmp extension
""" if self.gemini_ai else """
  AI Commands:
    AI functionality disabled - no API key provided
"""

        help_text = f"""
Enhanced Terminal with Gemini AI Integration

Available commands:
  File Operations:
    ls [options] [path]     - List directory contents
    cd [path]               - Change directory
    pwd                     - Print working directory
    mkdir <dir>             - Create directory
    rm [options] <file>     - Remove file
    rmdir <dir>             - Remove empty directory
    cp <src> <dst>          - Copy file
    mv <src> <dst>          - Move/rename file
    cat <file>              - Display file contents
    echo <text>             - Display text
    grep <pattern> <file>   - Search in files
    find <path> [options]   - Find files
    touch <file>            - Create empty file
  
  System Monitoring:
    ps                      - List processes
    top                     - Show top processes
    kill <pid>              - Kill process
    df                      - Show disk usage
    du <path>               - Show directory size
    free                    - Show memory usage
    uptime                  - Show system uptime
    whoami                  - Show current user
    date                    - Show current date/time
  
  Terminal:
    history                 - Show command history
    clear                   - Clear screen
    help                    - Show this help
    exit/quit               - Exit terminal
{ai_help}
  Aliases:
    ll = ls -la
    la = ls -la
    .. = cd ..
    ... = cd ../..
    h = history
    c = clear
    q = exit

Features:
  • Auto-completion and command history
  • Cross-platform compatibility
  • Colored output for better readability
  • Error handling and validation
  • AI-powered natural language processing (when API key provided)
        """
        return help_text.strip(), 0
    
    def _handle_touch(self, args: List[str]) -> Tuple[str, int]:
        """Handle touch command (create empty files) with multiple files."""
        if not args:
            return f"{Fore.RED}touch: missing operand{Style.RESET_ALL}", 1

        for pattern in args:
            matched_files = glob.glob(os.path.join(self.current_dir, pattern)) if '*' in pattern or '?' in pattern else [pattern]
            
            # If wildcard did not match any existing file, create the new file(s)
            if not matched_files or '*' in pattern or '?' in pattern:
                matched_files = [pattern]

            for file_path in matched_files:
                try:
                    with open(file_path, 'a'):
                        pass
                except PermissionError:
                    return f"{Fore.RED}touch: {file_path}: Permission denied{Style.RESET_ALL}", 1
                except Exception as e:
                    return f"{Fore.RED}touch: {file_path}: {str(e)}{Style.RESET_ALL}", 1

        return "", 0

    
    def _execute_system_command(self, command: str) -> Tuple[str, int]:
        """Execute system command using subprocess, expanding wildcards on Windows."""
        try:
            # Expand wildcards for Windows
            command_to_run = expand_wildcards(command)

            result = subprocess.run(
                command_to_run, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=self.current_dir,
                timeout=30
            )
            return result.stdout + result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return f"{Fore.RED}Command timed out{Style.RESET_ALL}", 1
        except Exception as e:
            return f"{Fore.RED}Command failed: {str(e)}{Style.RESET_ALL}", 1

    def run(self):
        """Main terminal loop."""
        print(f"{Fore.CYAN}Enhanced Python Terminal v2.0 with Gemini AI{Style.RESET_ALL}")
        
        if self.gemini_ai:
            print(f"{Fore.GREEN}✅ Gemini AI integration active{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 Try: 'ai show me all files' or 'smart create a backup folder'{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  Gemini AI integration disabled (no API key){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   To enable AI features, restart with: python terminal.py --api-key YOUR_KEY{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}Type 'help' for available commands or 'exit' to quit{Style.RESET_ALL}")
        print()
        
        while True:
            try:
                user_input = self.session.prompt(
                    self.display_prompt(),
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=self.command_completer
                )
                
                if not user_input.strip():
                    continue
                
                output, exit_code = self.execute_command(user_input)
                
                if output:
                    print(output)
                
                if exit_code == 0 and user_input.strip().lower() in ['exit', 'quit']:
                    break
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Use 'exit' to quit{Style.RESET_ALL}")
            except EOFError:
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")


def main():
    """Main entry point with command line argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Python Terminal with Gemini AI")
    parser.add_argument(
        '--api-key', 
        type=str, 
        default=None,
        help='Gemini API key for AI functionality'
    )
    parser.add_argument(
        '--env-key',
        action='store_true',
        help='Use GEMINI_API_KEY environment variable'
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = None
    if args.api_key:
        api_key = args.api_key
    elif args.env_key or not args.api_key:
        api_key = os.getenv('GEMINI_API_KEY')
    
    # Use your provided API key as fallback
    if not api_key:
        api_key = "AIzaSyByHRUxqliDq4rBaM3MycTpU9PiGe-v06I"
    
    terminal = EnhancedTerminal(gemini_api_key=api_key)
    terminal.run()


if __name__ == "__main__":
    main()
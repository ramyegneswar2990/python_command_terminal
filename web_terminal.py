
import json
import os
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

from terminal import EnhancedTerminal

load_dotenv()


app = Flask(__name__)
app.secret_key = 'enhanced_terminal_secret_key_2024'

# Store terminal instances per session
terminals = {}

def get_terminal():
    """Get or create terminal instance for current session."""
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    if session_id not in terminals:
        # Use your API key here or get from environment
        api_key = os.getenv('GEMINI_API_KEY')
        terminals[session_id] = EnhancedTerminal(gemini_api_key=api_key)
    
    return terminals[session_id]

@app.route('/')
def index():
    """Main terminal page."""
    return render_template('terminal.html')

@app.route('/api/execute', methods=['POST'])
def execute_command():
    """Execute a command via API."""
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'output': '', 'exit_code': 0, 'current_dir': '', 'ai_enabled': False})
        
        terminal = get_terminal()
        output, exit_code = terminal.execute_command(command)
        current_dir = terminal.current_dir
        ai_enabled = terminal.gemini_ai is not None
        
        return jsonify({
            'output': output,
            'exit_code': exit_code,
            'current_dir': current_dir,
            'ai_enabled': ai_enabled
        })
    except Exception as e:
        return jsonify({
            'output': f'Error: {str(e)}',
            'exit_code': 1,
            'current_dir': '',
            'ai_enabled': False
        })

@app.route('/api/ai', methods=['POST'])
def ai_command():
    """Handle AI-powered natural language commands."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'output': 'No query provided', 'exit_code': 1})
        
        terminal = get_terminal()
        if not terminal.gemini_ai:
            return jsonify({
                'output': 'AI functionality not available. Please provide a Gemini API key.',
                'exit_code': 1,
                'current_dir': terminal.current_dir
            })
        
        # Execute AI command
        output, exit_code = terminal._handle_ai_command(query.split())
        
        return jsonify({
            'output': output,
            'exit_code': exit_code,
            'current_dir': terminal.current_dir,
            'ai_enabled': True
        })
    except Exception as e:
        return jsonify({
            'output': f'AI Error: {str(e)}',
            'exit_code': 1,
            'current_dir': '',
            'ai_enabled': False
        })

@app.route('/api/history')
def get_history():
    """Get command history."""
    terminal = get_terminal()
    return jsonify({'history': terminal.command_history[-50:]})

@app.route('/api/status')
def get_status():
    """Get terminal status and AI availability."""
    terminal = get_terminal()
    return jsonify({
        'current_dir': terminal.current_dir,
        'ai_enabled': terminal.gemini_ai is not None,
        'history_count': len(terminal.command_history)
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the enhanced terminal HTML template
    template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Python Terminal with AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%);
            color: #00ff00;
            height: 100vh;
            overflow: hidden;
        }

        .terminal-container {
            height: 100vh;
            display: flex;
            flex-direction: column;
            padding: 10px;
        }

        .terminal-header {
            background: rgba(0, 255, 0, 0.1);
            padding: 10px;
            border-radius: 5px 5px 0 0;
            border: 1px solid #00ff00;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .terminal-title {
            font-size: 18px;
            font-weight: bold;
        }

        .ai-status {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .ai-indicator {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }

        .ai-enabled {
            background: rgba(255, 0, 255, 0.2);
            color: #ff00ff;
            border: 1px solid #ff00ff;
        }

        .ai-disabled {
            background: rgba(255, 255, 0, 0.2);
            color: #ffff00;
            border: 1px solid #ffff00;
        }

        .terminal-output {
            flex: 1;
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff00;
            border-top: none;
            padding: 15px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.4;
        }

        .terminal-input-container {
            display: flex;
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid #00ff00;
            border-top: none;
            border-radius: 0 0 5px 5px;
        }

        .terminal-prompt {
            padding: 15px;
            color: #00ff00;
            font-weight: bold;
            white-space: nowrap;
        }

        .terminal-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #00ff00;
            font-family: inherit;
            font-size: 14px;
            padding: 15px 5px 15px 0;
        }

        .ai-toggle-container {
            display: flex;
            gap: 10px;
            padding: 10px;
        }

        .ai-toggle-btn {
            padding: 8px 15px;
            background: rgba(0, 255, 0, 0.1);
            border: 1px solid #00ff00;
            color: #00ff00;
            border-radius: 5px;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.3s ease;
        }

        .ai-toggle-btn:hover {
            background: rgba(0, 255, 0, 0.2);
            transform: translateY(-2px);
        }

        .ai-toggle-btn.active {
            background: rgba(255, 0, 255, 0.2);
            border-color: #ff00ff;
            color: #ff00ff;
        }

        .command-output {
            margin-bottom: 10px;
        }

        .command-line {
            color: #00ff00;
            margin-bottom: 5px;
        }

        .ai-command-line {
            color: #ff00ff;
            margin-bottom: 5px;
        }

        .output-text {
            color: #ffffff;
            margin-left: 0;
        }

        .error-text {
            color: #ff4444;
        }

        .ai-processing {
            color: #00ffff;
            animation: blink 1s infinite;
        }

        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }

        .scrollbar::-webkit-scrollbar {
            width: 8px;
        }

        .scrollbar::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.5);
        }

        .scrollbar::-webkit-scrollbar-thumb {
            background: rgba(0, 255, 0, 0.5);
            border-radius: 4px;
        }

        .scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 255, 0, 0.8);
        }

        .help-text {
            color: #888888;
            font-size: 12px;
            margin-top: 5px;
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .terminal-header {
                flex-direction: column;
                gap: 10px;
            }

            .ai-status {
                width: 100%;
                justify-content: center;
            }

            .ai-toggle-container {
                flex-wrap: wrap;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="terminal-container">
        <div class="terminal-header">
            <div class="terminal-title">🖥️ Enhanced Python Terminal v2.0</div>
            <div class="ai-status">
                <div id="aiIndicator" class="ai-indicator ai-disabled">🤖 AI Loading...</div>
                <div id="currentDir" style="font-size: 12px; color: #888;">~/</div>
            </div>
        </div>
        
        <div class="ai-toggle-container">
            <button id="normalMode" class="ai-toggle-btn active">💻 Normal Mode</button>
            <button id="aiMode" class="ai-toggle-btn">🤖 AI Mode</button>
            <div class="help-text">
                Normal Mode: Traditional terminal commands | AI Mode: Natural language queries
            </div>
        </div>
        
        <div id="terminalOutput" class="terminal-output scrollbar"></div>
        
        <div class="terminal-input-container">
            <div id="terminalPrompt" class="terminal-prompt">user@terminal:~$ </div>
            <input type="text" id="terminalInput" class="terminal-input" 
                   placeholder="Type a command or switch to AI mode for natural language..." 
                   autocomplete="off">
        </div>
    </div>

    <script>
        class EnhancedTerminal {
            constructor() {
                this.output = document.getElementById('terminalOutput');
                this.input = document.getElementById('terminalInput');
                this.prompt = document.getElementById('terminalPrompt');
                this.aiIndicator = document.getElementById('aiIndicator');
                this.currentDirElement = document.getElementById('currentDir');
                this.normalModeBtn = document.getElementById('normalMode');
                this.aiModeBtn = document.getElementById('aiMode');
                
                this.isAiMode = false;
                this.aiEnabled = false;
                this.currentDir = '~';
                this.commandHistory = [];
                this.historyIndex = -1;
                
                this.init();
            }

            init() {
                this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
                this.normalModeBtn.addEventListener('click', () => this.setMode(false));
                this.aiModeBtn.addEventListener('click', () => this.setMode(true));
                
                this.checkStatus();
                this.addWelcomeMessage();
            }

            async checkStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    this.aiEnabled = data.ai_enabled;
                    this.currentDir = data.current_dir;
                    this.updateUI();
                } catch (error) {
                    console.error('Failed to check status:', error);
                }
            }

            updateUI() {
                // Update AI indicator
                if (this.aiEnabled) {
                    this.aiIndicator.textContent = '🤖 AI Ready';
                    this.aiIndicator.className = 'ai-indicator ai-enabled';
                } else {
                    this.aiIndicator.textContent = '🤖 AI Disabled';
                    this.aiIndicator.className = 'ai-indicator ai-disabled';
                }

                // Update current directory
                this.currentDirElement.textContent = this.currentDir;

                // Update prompt
                const dirName = this.currentDir.split('/').pop() || this.currentDir;
                const promptPrefix = this.isAiMode ? '🤖 AI' : 'user@terminal';
                this.prompt.textContent = `${promptPrefix}:${dirName}$ `;

                // Update input placeholder
                if (this.isAiMode && this.aiEnabled) {
                    this.input.placeholder = 'Ask AI: "show me all python files" or "create a backup folder"...';
                } else if (this.isAiMode && !this.aiEnabled) {
                    this.input.placeholder = 'AI mode disabled - no API key available';
                } else {
                    this.input.placeholder = 'Type a terminal command...';
                }
            }

            setMode(aiMode) {
                this.isAiMode = aiMode;
                
                if (aiMode) {
                    this.normalModeBtn.classList.remove('active');
                    this.aiModeBtn.classList.add('active');
                } else {
                    this.aiModeBtn.classList.remove('active');
                    this.normalModeBtn.classList.add('active');
                }
                
                this.updateUI();
                this.input.focus();
            }

            addWelcomeMessage() {
                const welcome = document.createElement('div');
                welcome.className = 'command-output';
                welcome.innerHTML = `
                    <div style="color: #00ffff; font-weight: bold; margin-bottom: 10px;">
                        🚀 Enhanced Python Terminal with Gemini AI Integration
                    </div>
                    <div style="color: #ffff00; margin-bottom: 5px;">
                        💡 Features:
                    </div>
                    <div style="color: #ffffff; margin-left: 20px; margin-bottom: 10px;">
                        • Traditional terminal commands (ls, cd, mkdir, etc.)
                        • AI-powered natural language processing
                        • System monitoring and file operations
                        • Command history and auto-completion
                    </div>
                    <div style="color: #ffff00; margin-bottom: 5px;">
                        🤖 AI Examples:
                    </div>
                    <div style="color: #ffffff; margin-left: 20px; margin-bottom: 10px;">
                        • "show me all python files"
                        • "create a backup folder and copy all text files to it"
                        • "find the largest files in this directory"
                        • "show me processes using more than 50% CPU"
                    </div>
                    <div style="color: #888888;">
                        Type 'help' for all commands or switch to AI mode for natural language queries.
                    </div>
                `;
                this.output.appendChild(welcome);
                this.scrollToBottom();
            }

            async handleKeydown(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    await this.executeCommand();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    this.navigateHistory(-1);
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.navigateHistory(1);
                }
            }

            async executeCommand() {
                const command = this.input.value.trim();
                if (!command) return;

                // Add command to history
                this.commandHistory.push(command);
                this.historyIndex = this.commandHistory.length;

                // Display command
                const commandDiv = document.createElement('div');
                commandDiv.className = 'command-output';
                
                const promptPrefix = this.isAiMode ? '🤖 AI' : 'user@terminal';
                const dirName = this.currentDir.split('/').pop() || this.currentDir;
                
                commandDiv.innerHTML = `<div class="${this.isAiMode ? 'ai-command-line' : 'command-line'}">${promptPrefix}:${dirName}$ ${command}</div>`;
                this.output.appendChild(commandDiv);

                // Clear input
                this.input.value = '';

                // Show processing for AI commands
                if (this.isAiMode && this.aiEnabled) {
                    const processingDiv = document.createElement('div');
                    processingDiv.className = 'ai-processing';
                    processingDiv.textContent = '🤖 AI is thinking...';
                    this.output.appendChild(processingDiv);
                    this.scrollToBottom();
                }

                try {
                    let response;
                    if (this.isAiMode && this.aiEnabled) {
                        response = await fetch('/api/ai', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ query: command })
                        });
                    } else {
                        // For AI mode without API key, prepend 'ai' to the command
                        const actualCommand = this.isAiMode && !this.aiEnabled ? `ai ${command}` : command;
                        response = await fetch('/api/execute', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ command: actualCommand })
                        });
                    }

                    const data = await response.json();

                    // Remove processing message
                    if (this.isAiMode && this.aiEnabled) {
                        const processingMsg = this.output.querySelector('.ai-processing');
                        if (processingMsg) {
                            processingMsg.remove();
                        }
                    }

                    // Display output
                    if (data.output) {
                        const outputDiv = document.createElement('div');
                        outputDiv.className = `output-text ${data.exit_code !== 0 ? 'error-text' : ''}`;
                        outputDiv.textContent = data.output;
                        this.output.appendChild(outputDiv);
                    }

                    // Update current directory
                    if (data.current_dir) {
                        this.currentDir = data.current_dir;
                        this.updateUI();
                    }

                } catch (error) {
                    // Remove processing message
                    const processingMsg = this.output.querySelector('.ai-processing');
                    if (processingMsg) {
                        processingMsg.remove();
                    }

                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'output-text error-text';
                    errorDiv.textContent = `Error: ${error.message}`;
                    this.output.appendChild(errorDiv);
                }

                this.scrollToBottom();
            }

            navigateHistory(direction) {
                if (this.commandHistory.length === 0) return;

                this.historyIndex += direction;
                
                if (this.historyIndex < 0) {
                    this.historyIndex = 0;
                } else if (this.historyIndex >= this.commandHistory.length) {
                    this.historyIndex = this.commandHistory.length;
                    this.input.value = '';
                    return;
                }

                this.input.value = this.commandHistory[this.historyIndex];
            }

            scrollToBottom() {
                this.output.scrollTop = this.output.scrollHeight;
            }
        }

        // Initialize terminal when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new EnhancedTerminal();
        });
    </script>
</body>
</html>"""
    
    # Write the template file
    with open('templates/terminal.html', 'w') as f:
        f.write(template_content)
    
    print("🚀 Enhanced Terminal Server Starting...")
    print(f"📱 Web Interface: http://localhost:5000")
    print(f"🤖 AI Integration: {'Enabled' if os.getenv('GEMINI_API_KEY') or True else 'Disabled'}")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
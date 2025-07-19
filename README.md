# MCP Video Editing Assistant

A Model Context Protocol (MCP) server that learns from your video editing behavior and provides intelligent assistance for film and television post-production workflows.

## Features

### 🎬 DaVinci Resolve Integration
- **Real-time Timeline Analysis**: Track cuts, transitions, and editing patterns
- **Workflow Learning**: Monitor tool usage across Edit, Color, Fairlight, and Deliver pages
- **AI-Powered Insights**: Get personalized suggestions based on your editing style

### 📊 Editing Behavior Tracking
- **Cut Pattern Analysis**: Learn your preferred cut lengths and rhythms
- **Session Monitoring**: Track editing sessions with detailed action logs
- **Workflow Optimization**: Identify bottlenecks and suggest improvements

### 🔧 Smart Tools
- **File Operations**: Automated media organization and project structure
- **Project Monitoring**: Watch for file changes and project updates
- **Pattern Recognition**: Detect editing habits and preferences

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-video-editing-assistant.git
cd mcp-video-editing-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_editing.txt
```

### 2. DaVinci Resolve Setup

```bash
# Run the setup script to configure Resolve API
python setup_resolve_integration.py
```

**Enable API Access in DaVinci Resolve:**
1. Open DaVinci Resolve
2. Go to Preferences > System > General
3. Enable "External Scripting Using"
4. Restart DaVinci Resolve

### 3. Claude Desktop Configuration

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "video-editing-assistant": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["/path/to/your/project/davinci_resolve_mcp.py"]
    },
    "editing-watcher": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["/path/to/your/project/editing_watcher.py"]
    }
  }
}
```

### 4. Usage

1. **Start DaVinci Resolve** with a project loaded
2. **Restart Claude Desktop** to load the MCP servers
3. **Begin learning session:**
   ```
   Ask Claude: "Connect to resolve and start learning my editing patterns"
   ```

## Available Tools

### DaVinci Resolve Integration
- `connect_to_resolve` - Connect to DaVinci Resolve API
- `analyze_current_timeline` - Analyze the active timeline
- `analyze_cut_patterns` - Get insights on your cutting style
- `track_tool_usage` - Monitor which tools you use most
- `get_editing_insights` - AI analysis of your editing patterns
- `suggest_workflow_optimization` - Get personalized workflow suggestions

### General Editing Tools
- `start_learning_session` - Begin tracking editing behavior
- `track_cut` - Manually log cut decisions and reasoning
- `track_workflow_step` - Monitor post-production phases
- `get_editing_insights` - View learned patterns and statistics
- `suggest_next_action` - AI-powered next step recommendations

### File Operations
- `file_write` - Create and modify files
- `list_files` - Browse project directories
- `run_command` - Execute system commands
- `get_timestamp` - Track timing information

## Examples

### Start Learning Your Editing Style
```
Ask Claude: "Start a learning session for my documentary project"
Claude will: Begin tracking your timeline changes, tool usage, and cutting patterns
```

### Get Editing Insights
```
Ask Claude: "What patterns do you see in my editing?"
Claude will: Analyze your cut lengths, tool preferences, and workflow habits
```

### Timeline Analysis
```
Ask Claude: "Analyze my current timeline in Resolve"
Claude will: Provide detailed statistics about cuts, pacing, and structure
```

### Workflow Optimization
```
Ask Claude: "How can I optimize my editing workflow?"
Claude will: Suggest keyboard shortcuts, tool recommendations, and efficiency improvements
```

## Project Structure

```
mcp-video-editing-assistant/
├── README.md
├── requirements.txt
├── requirements_editing.txt
├── server.py                    # Basic MCP server
├── enhanced_server.py           # Enhanced file operations server
├── editing_watcher.py           # General editing behavior tracker
├── davinci_resolve_mcp.py       # DaVinci Resolve integration
├── setup_resolve_integration.py # Setup and configuration script
└── claude_desktop_config*.json  # Configuration examples
```

## Requirements

### Software
- **Python 3.8+**
- **DaVinci Resolve 17+** (for Resolve integration)
- **Claude Desktop** with MCP support

### Python Dependencies
- `mcp` - Model Context Protocol framework
- `watchdog` - File system monitoring
- `xmltodict` - XML parsing for project files
- `opencv-python` - Video analysis (optional)
- `ffmpeg-python` - Media file processing (optional)

## Configuration

### Environment Variables
```bash
export RESOLVE_API_PATH="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/"
export EDITING_DATA_PATH="./editing_patterns.json"
```

### DaVinci Resolve API Paths
- **macOS**: `/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/`
- **Windows**: `C:\Program Files\Blackmagic Design\DaVinci Resolve\`
- **Linux**: `/opt/resolve/libs/Fusion/`

## Troubleshooting

### DaVinci Resolve Connection Issues
1. Ensure DaVinci Resolve is running
2. Check that API access is enabled in preferences
3. Verify the correct API path for your platform
4. Run `python setup_resolve_integration.py` to test connection

### MCP Server Not Loading
1. Check that Claude Desktop configuration is correct
2. Verify virtual environment Python path
3. Ensure all dependencies are installed
4. Check Claude Desktop logs for error messages

### Permission Issues
1. Ensure Python has permission to access project directories
2. Check file system permissions for media folders
3. Run with appropriate user privileges

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Anthropic** for the Model Context Protocol
- **Blackmagic Design** for the DaVinci Resolve API
- The **Claude Desktop** team for MCP integration

## Roadmap

- [ ] Adobe Premiere Pro integration
- [ ] Final Cut Pro X support
- [ ] Avid Media Composer compatibility
- [ ] AI-powered color grading suggestions
- [ ] Automated rough cut generation
- [ ] Export preset recommendations
- [ ] Collaboration workflow tools

---

**Note**: This project is for defensive security and productivity purposes only. Always follow industry best practices for media security and backup procedures.
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) Video Editing Assistant that integrates with DaVinci Resolve to learn from editing behavior and provide intelligent assistance for film/TV post-production workflows.

## Architecture

The project consists of three main MCP servers:

- **server.py**: Basic MCP server template with echo functionality
- **davinci_resolve_mcp.py**: DaVinci Resolve integration server with real-time timeline analysis, workflow learning, and AI-powered insights
- **editing_watcher.py**: General editing behavior tracker using file system monitoring
- **enhanced_server.py**: Enhanced file operations server

The architecture follows MCP patterns with async handlers for tools and resources. Each server tracks different aspects of editing workflows and maintains persistent data in JSON files.

## Key Components

### DaVinci Resolve Integration
- Uses DaVinci Resolve Python API (fusionscript)
- Tracks timeline changes, cut patterns, tool usage across Edit/Color/Fairlight/Deliver pages
- Platform-specific API paths: macOS (`/Applications/DaVinci Resolve/`), Windows (`C:\Program Files\Blackmagic Design\DaVinci Resolve\`), Linux (`/opt/resolve/libs/Fusion/`)

### Behavior Tracking
- `ResolveEditingTracker` class for DaVinci-specific tracking
- `EditingBehaviorTracker` class for general editing patterns
- File system monitoring with watchdog for project changes
- JSON persistence for learned patterns and insights

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements_editing.txt  # Full editing features
# or
pip install -r requirements.txt          # Basic MCP only
```

### DaVinci Resolve Setup
```bash
# Configure Resolve API integration
python setup_resolve_integration.py
```

### Running Servers
```bash
# Run individual MCP servers
python davinci_resolve_mcp.py
python editing_watcher.py
python enhanced_server.py
python server.py
```

### Testing
```bash
# Test Resolve connection
python -c "import sys; sys.path.append('/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/'); import DaVinciResolveScript as dvr; print('Resolve API available')"
```

## Claude Desktop Configuration

The servers are designed to run as MCP servers in Claude Desktop. Example configuration paths:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Each server should be configured with the virtual environment Python path and appropriate server script.

## Data Files

- `resolve_editing_patterns.json`: DaVinci Resolve-specific learning data
- `editing_patterns.json`: General editing behavior patterns
- Pattern files track sessions, cut analysis, workflow habits, and AI insights

## Dependencies

Core: `mcp>=1.0.0`
Editing features: `watchdog>=3.0.0`, `xmltodict>=0.13.0`, `opencv-python>=4.8.0`, `ffmpeg-python>=0.2.0`

## Platform Considerations

DaVinci Resolve API requires specific setup per platform and API access must be enabled in Resolve preferences (System > General > External Scripting Using).
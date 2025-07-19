#!/usr/bin/env python3
import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
from pydantic import AnyUrl
import mcp.types as types

server = Server("enhanced-mcp-server")

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources."""
    resources = []
    
    # Add current directory files as resources
    try:
        for file in os.listdir("."):
            if os.path.isfile(file) and file.endswith(('.txt', '.md', '.py', '.json')):
                resources.append(Resource(
                    uri=AnyUrl(f"file:///{file}"),
                    name=file,
                    description=f"Local file: {file}",
                    mimeType="text/plain",
                ))
    except Exception:
        pass
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource."""
    file_path = str(uri).replace("file:///", "")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Could not read file {file_path}: {e}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="file_write",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["filename", "content"],
            },
        ),
        Tool(
            name="list_files",
            description="List files in current directory",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="run_command",
            description="Run a shell command (use with caution)",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to run"},
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="get_timestamp",
            description="Get current timestamp",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls."""
    
    if name == "file_write":
        filename = arguments["filename"]
        content = arguments["content"]
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return [types.TextContent(type="text", text=f"Successfully wrote to {filename}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error writing file: {e}")]
    
    elif name == "list_files":
        try:
            files = os.listdir(".")
            file_list = "\n".join(files)
            return [types.TextContent(type="text", text=f"Files in current directory:\n{file_list}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error listing files: {e}")]
    
    elif name == "run_command":
        command = arguments["command"]
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            output = f"Exit code: {result.returncode}\n"
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}"
            return [types.TextContent(type="text", text=output)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error running command: {e}")]
    
    elif name == "get_timestamp":
        timestamp = datetime.now().isoformat()
        return [types.TextContent(type="text", text=f"Current timestamp: {timestamp}")]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
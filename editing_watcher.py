#!/usr/bin/env python3
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
import mcp.types as types
from pydantic import AnyUrl

class EditingBehaviorTracker:
    def __init__(self, data_file="editing_patterns.json"):
        self.data_file = data_file
        self.patterns = self.load_patterns()
        
    def load_patterns(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {
            "sessions": [],
            "cut_patterns": {},
            "timing_patterns": {},
            "workflow_sequences": [],
            "preferences": {}
        }
    
    def save_patterns(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)
    
    def track_session_start(self, project_path):
        session = {
            "project": project_path,
            "start_time": datetime.now().isoformat(),
            "actions": [],
            "cuts": [],
            "exports": []
        }
        self.patterns["sessions"].append(session)
        return len(self.patterns["sessions"]) - 1
    
    def track_action(self, session_id, action_type, details):
        if session_id < len(self.patterns["sessions"]):
            self.patterns["sessions"][session_id]["actions"].append({
                "timestamp": datetime.now().isoformat(),
                "type": action_type,
                "details": details
            })
            self.save_patterns()
    
    def analyze_cut_patterns(self):
        """Analyze cutting patterns across sessions"""
        cut_lengths = []
        cut_frequencies = {}
        
        for session in self.patterns["sessions"]:
            for cut in session.get("cuts", []):
                length = cut.get("duration", 0)
                if length > 0:
                    cut_lengths.append(length)
                    
                cut_type = cut.get("type", "unknown")
                cut_frequencies[cut_type] = cut_frequencies.get(cut_type, 0) + 1
        
        if cut_lengths:
            avg_cut_length = sum(cut_lengths) / len(cut_lengths)
            return {
                "average_cut_length": avg_cut_length,
                "total_cuts": len(cut_lengths),
                "cut_type_preferences": cut_frequencies,
                "suggested_cut_length": round(avg_cut_length, 2)
            }
        return {}

class ProjectFileWatcher(FileSystemEventHandler):
    def __init__(self, tracker, session_id):
        self.tracker = tracker
        self.session_id = session_id
        self.last_modified = {}
    
    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_ext = Path(file_path).suffix.lower()
            
            # Track project file changes
            if file_ext in ['.prproj', '.fcpxml', '.avp', '.drp']:
                current_time = time.time()
                if file_path not in self.last_modified or \
                   current_time - self.last_modified[file_path] > 2:  # Debounce
                    
                    self.tracker.track_action(self.session_id, "project_save", {
                        "file": file_path,
                        "file_type": file_ext,
                        "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    })
                    self.last_modified[file_path] = current_time

server = Server("editing-watcher")
tracker = EditingBehaviorTracker()
active_sessions = {}
file_observers = {}

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="start_learning_session",
            description="Start tracking editing behavior for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Path to project file or directory"},
                    "project_name": {"type": "string", "description": "Name of the project"}
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="stop_learning_session",
            description="Stop tracking current editing session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID to stop"}
                }
            }
        ),
        Tool(
            name="track_cut",
            description="Manually track a cut/edit decision",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "cut_type": {"type": "string", "enum": ["hard_cut", "fade", "dissolve", "jump_cut"]},
                    "duration": {"type": "number", "description": "Duration in seconds"},
                    "reason": {"type": "string", "description": "Why you made this cut"}
                },
                "required": ["session_id", "cut_type"]
            }
        ),
        Tool(
            name="get_editing_insights",
            description="Get learned patterns and suggestions",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="track_workflow_step",
            description="Track a workflow step (import, color, audio, export)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "step": {"type": "string", "enum": ["import", "rough_cut", "fine_cut", "color", "audio", "export"]},
                    "duration_minutes": {"type": "number"}
                },
                "required": ["session_id", "step"]
            }
        ),
        Tool(
            name="suggest_next_action",
            description="Get AI suggestion for next editing action based on patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_step": {"type": "string"},
                    "project_type": {"type": "string", "enum": ["documentary", "narrative", "commercial", "social_media"]}
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    
    if name == "start_learning_session":
        project_path = arguments["project_path"]
        project_name = arguments.get("project_name", Path(project_path).name)
        
        session_id = tracker.track_session_start(project_path)
        
        # Start file watching
        if os.path.exists(project_path):
            observer = Observer()
            event_handler = ProjectFileWatcher(tracker, session_id)
            
            if os.path.isdir(project_path):
                observer.schedule(event_handler, project_path, recursive=True)
            else:
                observer.schedule(event_handler, os.path.dirname(project_path), recursive=False)
            
            observer.start()
            file_observers[session_id] = observer
            
        active_sessions[str(session_id)] = {
            "project": project_name,
            "path": project_path,
            "start_time": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=f"Started learning session {session_id} for '{project_name}'. Now tracking your editing behavior!"
        )]
    
    elif name == "stop_learning_session":
        session_id = arguments.get("session_id")
        if session_id and session_id in active_sessions:
            # Stop file watching
            if int(session_id) in file_observers:
                file_observers[int(session_id)].stop()
                del file_observers[int(session_id)]
            
            project_name = active_sessions[session_id]["project"]
            del active_sessions[session_id]
            
            # Analyze this session
            insights = tracker.analyze_cut_patterns()
            
            return [types.TextContent(
                type="text",
                text=f"Stopped learning session for '{project_name}'. Session data saved and analyzed."
            )]
        else:
            return [types.TextContent(type="text", text="No active session found")]
    
    elif name == "track_cut":
        session_id = int(arguments["session_id"])
        cut_data = {
            "type": arguments["cut_type"],
            "duration": arguments.get("duration"),
            "reason": arguments.get("reason"),
            "timestamp": datetime.now().isoformat()
        }
        
        if session_id < len(tracker.patterns["sessions"]):
            tracker.patterns["sessions"][session_id]["cuts"].append(cut_data)
            tracker.save_patterns()
            
            return [types.TextContent(
                type="text",
                text=f"Tracked {arguments['cut_type']} cut for session {session_id}"
            )]
    
    elif name == "get_editing_insights":
        insights = tracker.analyze_cut_patterns()
        
        # Calculate session stats
        total_sessions = len(tracker.patterns["sessions"])
        avg_session_actions = 0
        if total_sessions > 0:
            total_actions = sum(len(s.get("actions", [])) for s in tracker.patterns["sessions"])
            avg_session_actions = total_actions / total_sessions
        
        workflow_patterns = {}
        for session in tracker.patterns["sessions"]:
            for action in session.get("actions", []):
                step = action.get("details", {}).get("step")
                if step:
                    workflow_patterns[step] = workflow_patterns.get(step, 0) + 1
        
        report = f"""# Your Editing Patterns

## Session Statistics
- Total editing sessions: {total_sessions}
- Average actions per session: {avg_session_actions:.1f}

## Cutting Patterns
{json.dumps(insights, indent=2) if insights else "Not enough cut data yet"}

## Workflow Preferences
{json.dumps(workflow_patterns, indent=2) if workflow_patterns else "No workflow data yet"}

## Recommendations
- Based on your patterns, you prefer {insights.get('cut_type_preferences', {}).get(max(insights.get('cut_type_preferences', {}), key=insights.get('cut_type_preferences', {}).get) if insights.get('cut_type_preferences') else 'unknown')} cuts
- Your average cut length is {insights.get('average_cut_length', 'unknown')} seconds
"""
        
        return [types.TextContent(type="text", text=report)]
    
    elif name == "track_workflow_step":
        session_id = int(arguments["session_id"])
        tracker.track_action(session_id, "workflow_step", {
            "step": arguments["step"],
            "duration_minutes": arguments.get("duration_minutes")
        })
        
        return [types.TextContent(
            type="text",
            text=f"Tracked {arguments['step']} workflow step"
        )]
    
    elif name == "suggest_next_action":
        current_step = arguments.get("current_step", "")
        project_type = arguments.get("project_type", "")
        
        # Analyze patterns to suggest next action
        suggestions = []
        
        if current_step == "rough_cut":
            avg_cut = tracker.analyze_cut_patterns().get("suggested_cut_length")
            if avg_cut:
                suggestions.append(f"Based on your style, consider {avg_cut}s cuts")
        
        elif current_step == "import":
            suggestions.append("Based on your workflow, you typically move to rough_cut next")
        
        if not suggestions:
            suggestions.append("Continue with your normal workflow - I'm still learning your patterns!")
        
        return [types.TextContent(
            type="text", 
            text=f"Suggestions for {current_step}:\n" + "\n".join(f"• {s}" for s in suggestions)
        )]
    
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
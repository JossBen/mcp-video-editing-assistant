#!/usr/bin/env python3
import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
import mcp.types as types
from pydantic import AnyUrl

# DaVinci Resolve API setup
try:
    # Add DaVinci Resolve Python API path
    if sys.platform.startswith("darwin"):  # macOS
        resolve_path = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
        sys.path.append("/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/")
    elif sys.platform.startswith("win"):  # Windows
        resolve_path = "C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\fusionscript.dll"
        sys.path.append("C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\")
    else:  # Linux
        resolve_path = "/opt/resolve/libs/Fusion/fusionscript.so"
        sys.path.append("/opt/resolve/libs/Fusion/")
    
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
    
except ImportError:
    print("DaVinci Resolve API not found. Make sure DaVinci Resolve is installed.")
    resolve = None

class ResolveEditingTracker:
    def __init__(self, data_file="resolve_editing_patterns.json"):
        self.data_file = data_file
        self.patterns = self.load_patterns()
        self.current_project = None
        self.last_timeline_state = {}
        
    def load_patterns(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {
            "editing_sessions": [],
            "cut_analysis": {},
            "color_patterns": {},
            "audio_patterns": {},
            "workflow_habits": {},
            "tool_usage": {}
        }
    
    def save_patterns(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)
    
    def analyze_current_timeline(self):
        """Analyze current timeline state in Resolve"""
        if not resolve:
            return {"error": "Resolve API not available"}
        
        try:
            project = resolve.GetProjectManager().GetCurrentProject()
            if not project:
                return {"error": "No project loaded"}
            
            timeline = project.GetCurrentTimeline()
            if not timeline:
                return {"error": "No timeline selected"}
            
            timeline_data = {
                "name": timeline.GetName(),
                "frame_rate": timeline.GetSetting("timelineFrameRate"),
                "resolution": f"{timeline.GetSetting('timelineResolutionWidth')}x{timeline.GetSetting('timelineResolutionHeight')}",
                "track_count": timeline.GetTrackCount("video") + timeline.GetTrackCount("audio"),
                "duration": timeline.GetDuration(),
                "clips": []
            }
            
            # Analyze clips on timeline
            for track_type in ["video", "audio"]:
                track_count = timeline.GetTrackCount(track_type)
                for track_index in range(1, track_count + 1):
                    clips = timeline.GetItemsInTrack(track_type, track_index)
                    for clip_id, clip_info in clips.items():
                        clip_data = {
                            "track_type": track_type,
                            "track_index": track_index,
                            "start": clip_info.get("start", 0),
                            "end": clip_info.get("end", 0),
                            "duration": clip_info.get("duration", 0),
                            "name": clip_info.get("mediaPoolItem", {}).get("name", ""),
                        }
                        timeline_data["clips"].append(clip_data)
            
            return timeline_data
            
        except Exception as e:
            return {"error": f"Timeline analysis failed: {str(e)}"}
    
    def track_editing_action(self, action_type, details):
        """Track an editing action with timestamp"""
        action = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "details": details
        }
        
        if not self.patterns["editing_sessions"]:
            self.patterns["editing_sessions"].append({
                "start_time": datetime.now().isoformat(),
                "actions": []
            })
        
        self.patterns["editing_sessions"][-1]["actions"].append(action)
        self.save_patterns()
    
    def analyze_cut_patterns(self):
        """Analyze cutting patterns from timeline data"""
        cut_lengths = []
        cut_types = {}
        
        timeline_data = self.analyze_current_timeline()
        if "error" in timeline_data:
            return timeline_data
        
        clips = timeline_data.get("clips", [])
        video_clips = [c for c in clips if c["track_type"] == "video"]
        
        # Sort clips by start time
        video_clips.sort(key=lambda x: x["start"])
        
        for i, clip in enumerate(video_clips):
            duration = clip["duration"]
            if duration > 0:
                cut_lengths.append(duration)
                
            # Detect cut types based on transitions
            if i > 0:
                prev_clip = video_clips[i-1]
                gap = clip["start"] - prev_clip["end"]
                
                if gap == 0:
                    cut_types["hard_cut"] = cut_types.get("hard_cut", 0) + 1
                elif gap > 0:
                    cut_types["gap"] = cut_types.get("gap", 0) + 1
                else:
                    cut_types["overlap"] = cut_types.get("overlap", 0) + 1
        
        if cut_lengths:
            return {
                "total_cuts": len(cut_lengths),
                "average_cut_length": sum(cut_lengths) / len(cut_lengths),
                "shortest_cut": min(cut_lengths),
                "longest_cut": max(cut_lengths),
                "cut_types": cut_types,
                "median_cut_length": sorted(cut_lengths)[len(cut_lengths)//2],
                "editing_pace": "fast" if sum(cut_lengths) / len(cut_lengths) < 120 else "slow"
            }
        
        return {"error": "No cuts found"}

server = Server("davinci-resolve-watcher")
tracker = ResolveEditingTracker()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="connect_to_resolve",
            description="Connect to DaVinci Resolve and verify API access",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="analyze_current_timeline",
            description="Analyze the currently open timeline in Resolve",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="track_editing_session",
            description="Start tracking editing behavior in current project",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_project_info",
            description="Get information about current Resolve project",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="analyze_cut_patterns",
            description="Analyze cutting patterns in current timeline",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_color_grading_info",
            description="Analyze color grading applied to clips",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="track_tool_usage",
            description="Track which Resolve tools are being used",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Name of the tool used"},
                    "page": {"type": "string", "enum": ["edit", "cut", "fusion", "color", "fairlight", "deliver"]}
                },
                "required": ["tool_name", "page"]
            }
        ),
        Tool(
            name="export_timeline_data",
            description="Export detailed timeline data for analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {"type": "string", "enum": ["json", "csv", "xml"], "default": "json"}
                }
            }
        ),
        Tool(
            name="get_editing_insights",
            description="Get AI insights about your editing patterns",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="suggest_workflow_optimization",
            description="Get suggestions to optimize your Resolve workflow",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    
    if name == "connect_to_resolve":
        if not resolve:
            return [types.TextContent(
                type="text",
                text="❌ DaVinci Resolve API not available. Please ensure:\n1. DaVinci Resolve is installed\n2. DaVinci Resolve is running\n3. API access is enabled in preferences"
            )]
        
        try:
            version = resolve.GetVersion()
            project_manager = resolve.GetProjectManager()
            current_project = project_manager.GetCurrentProject()
            
            status = f"✅ Connected to DaVinci Resolve {version}\n"
            if current_project:
                status += f"📁 Current project: {current_project.GetName()}\n"
                timeline = current_project.GetCurrentTimeline()
                if timeline:
                    status += f"🎬 Current timeline: {timeline.GetName()}"
                else:
                    status += "⚠️ No timeline selected"
            else:
                status += "⚠️ No project loaded"
            
            return [types.TextContent(type="text", text=status)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Failed to connect: {str(e)}"
            )]
    
    elif name == "analyze_current_timeline":
        timeline_data = tracker.analyze_current_timeline()
        
        if "error" in timeline_data:
            return [types.TextContent(type="text", text=f"Error: {timeline_data['error']}")]
        
        analysis = f"""# Timeline Analysis: {timeline_data['name']}

## Technical Specs
- Frame Rate: {timeline_data['frame_rate']} fps
- Resolution: {timeline_data['resolution']}
- Total Tracks: {timeline_data['track_count']}
- Duration: {timeline_data['duration']} frames

## Content Overview
- Total Clips: {len(timeline_data['clips'])}
- Video Clips: {len([c for c in timeline_data['clips'] if c['track_type'] == 'video'])}
- Audio Clips: {len([c for c in timeline_data['clips'] if c['track_type'] == 'audio'])}
"""
        
        tracker.track_editing_action("timeline_analysis", timeline_data)
        return [types.TextContent(type="text", text=analysis)]
    
    elif name == "get_project_info":
        if not resolve:
            return [types.TextContent(type="text", text="Resolve API not available")]
        
        try:
            project = resolve.GetProjectManager().GetCurrentProject()
            if not project:
                return [types.TextContent(type="text", text="No project loaded")]
            
            info = {
                "name": project.GetName(),
                "frame_rate": project.GetSetting("timelineFrameRate"),
                "timeline_count": len(project.GetTimelineList()),
                "media_pool_clips": len(project.GetMediaPool().GetRootFolder().GetClipList()),
            }
            
            return [types.TextContent(
                type="text",
                text=f"Project: {info['name']}\nTimelines: {info['timeline_count']}\nMedia Pool Clips: {info['media_pool_clips']}"
            )]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting project info: {str(e)}")]
    
    elif name == "analyze_cut_patterns":
        patterns = tracker.analyze_cut_patterns()
        
        if "error" in patterns:
            return [types.TextContent(type="text", text=f"Error: {patterns['error']}")]
        
        analysis = f"""# Cut Pattern Analysis

## Statistics
- Total Cuts: {patterns['total_cuts']}
- Average Cut Length: {patterns['average_cut_length']:.1f} frames
- Median Cut Length: {patterns['median_cut_length']} frames
- Shortest Cut: {patterns['shortest_cut']} frames
- Longest Cut: {patterns['longest_cut']} frames
- Editing Pace: {patterns['editing_pace']}

## Cut Types
{json.dumps(patterns['cut_types'], indent=2)}
"""
        
        tracker.track_editing_action("cut_analysis", patterns)
        return [types.TextContent(type="text", text=analysis)]
    
    elif name == "track_tool_usage":
        tool_name = arguments["tool_name"]
        page = arguments["page"]
        
        tool_data = {
            "tool": tool_name,
            "page": page,
            "timestamp": datetime.now().isoformat()
        }
        
        if page not in tracker.patterns["tool_usage"]:
            tracker.patterns["tool_usage"][page] = {}
        
        tracker.patterns["tool_usage"][page][tool_name] = \
            tracker.patterns["tool_usage"][page].get(tool_name, 0) + 1
        
        tracker.track_editing_action("tool_usage", tool_data)
        
        return [types.TextContent(
            type="text",
            text=f"Tracked usage of {tool_name} in {page} page"
        )]
    
    elif name == "get_editing_insights":
        sessions = tracker.patterns["editing_sessions"]
        tool_usage = tracker.patterns["tool_usage"]
        
        # Generate insights
        insights = []
        
        if sessions:
            total_actions = sum(len(s.get("actions", [])) for s in sessions)
            avg_actions = total_actions / len(sessions) if sessions else 0
            insights.append(f"You've completed {len(sessions)} editing sessions with an average of {avg_actions:.1f} actions per session")
        
        # Most used tools
        all_tools = {}
        for page, tools in tool_usage.items():
            for tool, count in tools.items():
                all_tools[f"{page}:{tool}"] = count
        
        if all_tools:
            most_used = max(all_tools.items(), key=lambda x: x[1])
            insights.append(f"Your most used tool is {most_used[0]} ({most_used[1]} times)")
        
        # Timeline analysis insights
        timeline_patterns = tracker.analyze_cut_patterns()
        if "error" not in timeline_patterns:
            insights.append(f"Your current editing pace is {timeline_patterns.get('editing_pace', 'unknown')}")
            insights.append(f"Average cut length: {timeline_patterns.get('average_cut_length', 0):.1f} frames")
        
        if not insights:
            insights.append("Keep editing! I'm still learning your patterns.")
        
        return [types.TextContent(
            type="text",
            text="# Your Editing Insights\n\n" + "\n".join(f"• {insight}" for insight in insights)
        )]
    
    elif name == "suggest_workflow_optimization":
        suggestions = []
        
        # Analyze current patterns for suggestions
        tool_usage = tracker.patterns["tool_usage"]
        
        # Suggest keyboard shortcuts for frequently used tools
        for page, tools in tool_usage.items():
            for tool, count in tools.items():
                if count > 10:  # Frequently used
                    suggestions.append(f"Consider learning keyboard shortcuts for {tool} in {page} page (used {count} times)")
        
        # Timeline-based suggestions
        timeline_patterns = tracker.analyze_cut_patterns()
        if "error" not in timeline_patterns:
            if timeline_patterns.get("editing_pace") == "fast":
                suggestions.append("Your fast editing pace suggests using the Cut page for quicker edits")
            
            avg_cut = timeline_patterns.get("average_cut_length", 0)
            if avg_cut > 0:
                suggestions.append(f"Your average cut length of {avg_cut:.1f} frames suggests {['quick', 'medium', 'slow'][min(2, int(avg_cut/100))]} paced content")
        
        if not suggestions:
            suggestions.append("Keep editing! I'll provide more specific suggestions as I learn your patterns.")
        
        return [types.TextContent(
            type="text",
            text="# Workflow Optimization Suggestions\n\n" + "\n".join(f"• {suggestion}" for suggestion in suggestions)
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
#!/usr/bin/env python3
"""
Setup script for DaVinci Resolve MCP integration
Helps configure the API paths and test connection
"""

import os
import sys
import platform

def setup_resolve_api():
    """Setup DaVinci Resolve API paths for different platforms"""
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        api_path = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/"
        script_path = os.path.join(api_path, "fusionscript.so")
        
        print("🍎 macOS detected")
        print(f"Looking for Resolve API at: {api_path}")
        
        if os.path.exists(script_path):
            print("✅ DaVinci Resolve API found!")
            return api_path
        else:
            print("❌ DaVinci Resolve not found. Please install DaVinci Resolve.")
            return None
            
    elif system == "Windows":
        api_path = "C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\"
        script_path = os.path.join(api_path, "fusionscript.dll")
        
        print("🪟 Windows detected")
        print(f"Looking for Resolve API at: {api_path}")
        
        if os.path.exists(script_path):
            print("✅ DaVinci Resolve API found!")
            return api_path
        else:
            print("❌ DaVinci Resolve not found. Please install DaVinci Resolve.")
            return None
            
    elif system == "Linux":
        api_path = "/opt/resolve/libs/Fusion/"
        script_path = os.path.join(api_path, "fusionscript.so")
        
        print("🐧 Linux detected")
        print(f"Looking for Resolve API at: {api_path}")
        
        if os.path.exists(script_path):
            print("✅ DaVinci Resolve API found!")
            return api_path
        else:
            print("❌ DaVinci Resolve not found. Please install DaVinci Resolve.")
            return None
    
    else:
        print(f"❌ Unsupported platform: {system}")
        return None

def test_resolve_connection():
    """Test connection to DaVinci Resolve"""
    
    api_path = setup_resolve_api()
    if not api_path:
        return False
    
    try:
        # Add to Python path
        if api_path not in sys.path:
            sys.path.append(api_path)
        
        print("\n🔄 Testing Resolve connection...")
        
        # Try to import and connect
        import DaVinciResolveScript as dvr_script
        resolve = dvr_script.scriptapp("Resolve")
        
        if resolve:
            version = resolve.GetVersion()
            print(f"✅ Connected to DaVinci Resolve {version}")
            
            # Test project access
            project_manager = resolve.GetProjectManager()
            current_project = project_manager.GetCurrentProject()
            
            if current_project:
                project_name = current_project.GetName()
                print(f"📁 Current project: {project_name}")
                
                # Test timeline access
                timeline = current_project.GetCurrentTimeline()
                if timeline:
                    timeline_name = timeline.GetName()
                    print(f"🎬 Current timeline: {timeline_name}")
                else:
                    print("⚠️ No timeline selected (this is OK)")
            else:
                print("⚠️ No project loaded (this is OK)")
            
            return True
            
        else:
            print("❌ Could not connect to Resolve. Make sure:")
            print("   1. DaVinci Resolve is running")
            print("   2. API access is enabled in Resolve preferences")
            return False
            
    except ImportError as e:
        print(f"❌ Could not import Resolve API: {e}")
        print("Make sure DaVinci Resolve is properly installed.")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure DaVinci Resolve is running and API is enabled.")
        return False

def create_resolve_config():
    """Create configuration for Claude Desktop"""
    
    config = {
        "mcpServers": {
            "davinci-resolve-watcher": {
                "command": f"{sys.executable}",
                "args": [os.path.abspath("davinci_resolve_mcp.py")]
            }
        }
    }
    
    config_path = "claude_desktop_config_resolve.json"
    
    with open(config_path, 'w') as f:
        import json
        json.dump(config, f, indent=2)
    
    print(f"\n📄 Created config file: {config_path}")
    print("\nTo use this configuration:")
    
    if platform.system() == "Darwin":
        claude_config_path = "~/Library/Application Support/Claude/claude_desktop_config.json"
    elif platform.system() == "Windows":
        claude_config_path = "%APPDATA%\\Claude\\claude_desktop_config.json"
    else:
        claude_config_path = "~/.config/claude/claude_desktop_config.json"
    
    print(f"1. Copy contents to: {claude_config_path}")
    print("2. Restart Claude Desktop")
    print("3. Start DaVinci Resolve")
    print("4. Ask Claude to 'connect to resolve'")

if __name__ == "__main__":
    print("🎬 DaVinci Resolve MCP Integration Setup")
    print("=" * 50)
    
    # Test API availability
    api_available = test_resolve_connection()
    
    if api_available:
        print("\n🎉 Setup successful!")
        create_resolve_config()
    else:
        print("\n❌ Setup incomplete. Please:")
        print("1. Install DaVinci Resolve")
        print("2. Start DaVinci Resolve")
        print("3. Enable API access in Preferences > System > General > External Scripting Using")
        print("4. Run this setup again")
    
    print("\n" + "=" * 50)
#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import json

DEFAULT_CONFIG_PATH = "./config.json"

def check_requirements():
    """Check if all required modules are installed."""
    try:
        import discord
        import aiohttp
        from PIL import Image
        return True
    except ImportError as e:
        print(f"Error: Missing required module - {e.name}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_config(config_path):
    """Check if the configuration file exists and has required fields."""
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found at {config_path}")
        print("Please run setup.py first")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_fields = ["token", "prefix", "videos_dir", "db_path"]
        for field in required_fields:
            if field not in config or not config[field]:
                print(f"Error: Missing required configuration field: {field}")
                print("Please edit your config.json file")
                return False
        
        return True
    
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in configuration file: {config_path}")
        return False
    except Exception as e:
        print(f"Error checking configuration: {e}")
        return False

def check_files():
    """Check if all required Python files exist."""
    required_files = ["main_bot.py", "db_utils.py", "hw_accel.py", "selfbot_embeds.py"]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"Error: Required file not found: {file}")
            return False
    
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start the StreamBot Discord selfbot")
    parser.add_argument("--config", "-c", type=str, default=DEFAULT_CONFIG_PATH,
                       help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})")
    parser.add_argument("--debug", "-d", action="store_true",
                       help="Enable debug mode (more verbose logging)")
    args = parser.parse_args()
    
    print("=== StreamBot Launcher ===\n")
    
    # Check requirements and files
    if not check_requirements():
        return
    
    if not check_files():
        return
    
    if not check_config(args.config):
        return
    
    # Start the bot
    cmd = [sys.executable, "main_bot.py"]
    
    if args.config != DEFAULT_CONFIG_PATH:
        cmd.extend(["--config", args.config])
    
    if args.debug:
        cmd.append("--debug")
        print("Starting bot in debug mode...")
    else:
        print("Starting bot...")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    main()

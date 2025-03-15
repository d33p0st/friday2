import re
import json
import os
from typing import Dict, List, Tuple, Optional, Callable
from difflib import get_close_matches
import time
import webbrowser

from friday2 import CONFIGURATION

class CommandParser:
    def __init__(self, commands_file: str = CONFIGURATION.joinpath('commands.json').__str__()):
        """
        Initialize the command parser with predefined commands.
        
        Args:
            commands_file: Path to JSON file containing command definitions
        """
        self.commands = self._load_commands(commands_file)
        self.command_history = []
        self.context = {}
        
    def _load_commands(self, commands_file: str) -> Dict:
        """Load commands from JSON file or create default commands"""
        if os.path.exists(commands_file):
            with open(commands_file, 'r') as f:
                return json.load(f)
        else:
            # Default commands if file doesn't exist
            default_commands = {
                "open": {
                    "patterns": [
                        r"open\s+(\w+(?:\s+\w+)*)",
                        r"launch\s+(\w+(?:\s+\w+)*)",
                        r"start\s+(\w+(?:\s+\w+)*)"
                    ],
                    "apps": {
                        "github": "github.com",
                        "browser": "web_browser",
                        "terminal": "terminal",
                        "vs code": "vscode",
                        "cursor": "cursor_editor",
                        "word": "ms_word",
                        "instagram": "instagram.com"
                    },
                    "function": "open_application"
                },
                "find_file": {
                    "patterns": [
                        r"find\s+(?:the\s+)?(?:file|files)?\s+(?:named|called)?\s+[\"']?([^\"']+)[\"']?(?:\s+in\s+(.+))?",
                        r"locate\s+(?:the\s+)?(?:file|files)?\s+(?:named|called)?\s+[\"']?([^\"']+)[\"']?(?:\s+in\s+(.+))?",
                        r"find\s+[\"']?([^\"']+)[\"']?(?:\s+in\s+(.+))?",
                        r"where\s+(?:is|are)\s+(?:the\s+)?(?:file|files)?\s+[\"']?([^\"']+)[\"']?(?:\s+in\s+(.+))?"
                    ],
                    "function": "find_files"
                },
                "web_search": {
                    "patterns": [
                        r"search\s+(?:the\s+)?(?:web|internet|online)\s+for\s+(.+)",
                        r"look\s+up\s+online\s+(.+)",
                        r"google\s+(.+)"
                    ],
                    "function": "web_search"
                },
                "system": {
                    "patterns": [
                        r"shut\s*down(?:\s+(?:the\s+)?system)?",
                        r"reboot(?:\s+(?:the\s+)?system)?",
                        r"restart(?:\s+(?:the\s+)?system)?"
                    ],
                    "function": "system_control"
                },
                "create": {
                    "patterns": [
                        r"create\s+(?:a\s+)?(?:new\s+)?(\w+(?:\s+\w+)*)\s+(?:named|called)?\s+[\"']?([^\"']+)[\"']?(?:\s+in\s+(.+))?",
                        r"make\s+(?:a\s+)?(?:new\s+)?(\w+(?:\s+\w+)*)\s+(?:named|called)?\s+[\"']?([^\"']+)[\"']?(?:\s+in\s+(.+))?",
                        r"new\s+(\w+(?:\s+\w+)*)\s+(?:named|called)?\s+[\"']?([^\"']+)[\"']?(?:\s+in\s+(.+))?"
                    ],
                    "types": ["project", "file", "folder", "directory", "document", "spreadsheet", 
                             "presentation", "text file", "python file", "javascript file", "html file", 
                             "css file", "markdown file", "json file", "yaml file", "xml file", 
                             "database", "script", "note", "todo list", "reminder"],
                    "function": "create_item"
                },
                "wifi": {
                    "patterns": [
                        r"(connect|disconnect)(?:\s+(?:from|to))?\s+(?:the\s+)?wi-?fi",
                        r"turn\s+(on|off)\s+(?:the\s+)?wi-?fi"
                    ],
                    "function": "control_wifi"
                },
                "timer": {
                    "patterns": [
                        r"set\s+(?:a\s+)?timer\s+for\s+(\d+)\s+(second|minute|hour)s?",
                        r"remind\s+me\s+in\s+(\d+)\s+(second|minute|hour)s?"
                    ],
                    "function": "set_timer"
                }
            }
            
            # Save default commands to file
            with open(commands_file, 'w') as f:
                json.dump(default_commands, f, indent=4)
                
            return default_commands
            
    def parse(self, transcription: str) -> Dict:
        """
        Parse the transcribed text and extract commands.
        Assumes the trigger phrase detection has already been handled.
        
        Args:
            transcription: The transcribed text from speech recognition
            
        Returns:
            Dictionary containing command info or None if no command detected
        """
        # Normalize text for easier matching
        text = transcription.lower().strip()
        
        # Match command patterns directly (no trigger phrase detection)
        result = self._match_command_patterns(text)
        
        # Log the command
        if result:
            self.command_history.append({
                "time": time.time(),
                "transcription": transcription,
                "command": result
            })
            
        return result if result else {"command": "unknown", "transcription": transcription}
    
    def _match_command_patterns(self, text: str) -> Optional[Dict]:
        """Match the text against command patterns"""
        for cmd_type, cmd_config in self.commands.items():
            patterns = cmd_config.get("patterns", [])
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result = {
                        "command": cmd_type,
                        "function": cmd_config.get("function"),
                        "params": match.groups(),
                        "raw_text": text
                    }
                    
                    # Special handling for app opening
                    if cmd_type == "open" and match.groups():
                        app_name = match.group(1).lower()
                        apps_dict = cmd_config.get("apps", {})
                        
                        # Try exact match first
                        if app_name in apps_dict:
                            result["target"] = apps_dict[app_name]
                        else:
                            # Try fuzzy matching
                            close_matches = get_close_matches(app_name, apps_dict.keys(), n=1, cutoff=0.7)
                            if close_matches:
                                result["target"] = apps_dict[close_matches[0]]
                                result["matched_name"] = close_matches[0]
                            else:
                                # No match found, use the raw name
                                result["target"] = app_name
                    
                    # Special handling for create command
                    if cmd_type == "create" and match.groups():
                        item_type = match.group(1).lower()
                        item_name = match.group(2)
                        location = match.group(3) if len(match.groups()) > 2 and match.group(3) else "current directory"
                        
                        # Add additional info to result
                        result["item_type"] = item_type
                        result["item_name"] = item_name
                        result["location"] = location
                        
                    # Special handling for find_file command
                    if cmd_type == "find_file" and match.groups():
                        file_pattern = match.group(1)
                        location = match.group(2) if len(match.groups()) > 1 and match.group(2) else "."
                        
                        result["file_pattern"] = file_pattern
                        result["location"] = location
                                
                    return result
        
        # If no pattern matched, try to infer the intent
        return self._infer_intent(text)
    
    def _infer_intent(self, text: str) -> Optional[Dict]:
        """Infer the command intent from free-form text"""
        # Simple keyword-based intent detection
        keywords = {
            "open": ["open", "launch", "start", "run"],
            "find_file": ["find", "locate", "where is", "search for file"],
            "web_search": ["search web", "look up online", "google", "browser search"],
            "system": ["shutdown", "restart", "reboot", "turn off"],
            "create": ["create", "make", "new", "generate"],
            "wifi": ["wifi", "internet", "connect", "disconnect"],
            "timer": ["timer", "remind", "alarm"]
        }
        
        # Find which keywords appear in the text
        scores = {cmd: 0 for cmd in keywords}
        for cmd, words in keywords.items():
            for word in words:
                if word in text:
                    scores[cmd] += 1
        
        # Get the command with the highest score, if any
        if max(scores.values()) > 0:
            best_cmd = max(scores, key=scores.get)
            return {
                "command": best_cmd,
                "function": self.commands.get(best_cmd, {}).get("function"),
                "inferred": True,
                "confidence": scores[best_cmd] / len(keywords[best_cmd]),
                "raw_text": text
            }
        
        return None
    
    def add_command(self, cmd_type: str, patterns: List[str], function: str, **kwargs) -> None:
        """Add a new command to the system"""
        if cmd_type not in self.commands:
            self.commands[cmd_type] = {
                "patterns": patterns,
                "function": function,
                **kwargs
            }
        else:
            # Update existing command
            self.commands[cmd_type]["patterns"].extend(patterns)
            self.commands[cmd_type]["function"] = function
            for k, v in kwargs.items():
                if k in self.commands[cmd_type] and isinstance(v, dict):
                    # Merge dictionaries
                    self.commands[cmd_type][k].update(v)
                else:
                    self.commands[cmd_type][k] = v
        
        # Save commands to file
        with open("commands.json", 'w') as f:
            json.dump(self.commands, f, indent=4)
    
    def get_suggestions(self, partial_command: str) -> List[str]:
        """Get suggestions for partial commands"""
        suggestions = []
        for cmd_type, cmd_config in self.commands.items():
            # TODO: Implement suggestion logic
            pass
        return suggestions


class CommandExecutor:
    def __init__(self, parser: CommandParser):
        """Initialize the command executor"""
        self.parser = parser
        self.function_map = {
            "open_application": self.open_application,
            "web_search": self.web_search,
            "system_control": self.system_control,
            "create_item": self.create_item,
            "control_wifi": self.control_wifi,
            "set_timer": self.set_timer,
            "find_files": self.find_files
        }
        
    def execute(self, transcription: str) -> Dict:
        """Execute a command from transcription"""
        # Parse the command
        cmd_data = self.parser.parse(transcription)
        
        result = {
            "success": False,
            "command_data": cmd_data,
            "message": "Command not recognized"
        }
        
        # If command is recognized, execute the corresponding function
        if cmd_data and cmd_data.get("command") != "unknown":
            func_name = cmd_data.get("function")
            if func_name in self.function_map:
                try:
                    function_result = self.function_map[func_name](cmd_data)
                    result.update({
                        "success": True,
                        "result": function_result,
                        "message": f"Executed {cmd_data.get('command')} command"
                    })
                except Exception as e:
                    result.update({
                        "success": False,
                        "error": str(e),
                        "message": f"Error executing {cmd_data.get('command')} command"
                    })
            else:
                result["message"] = f"Function {func_name} not implemented"
        
        return result
    
    # Command implementation functions
    def open_application(self, cmd_data: Dict) -> Dict:
        """Open an application or website"""
        target = cmd_data.get("target", "")
        print(f"[FRIDAY] Opening {target}...")
        # In a real implementation, you would add code to open the app or website

        if 'github' in target:
            status = webbrowser.open("https://github.com/d33p0st", 2)

        return {"target": target, "status": status}
    
    def web_search(self, cmd_data: Dict) -> Dict:
        """Perform a web search"""
        query = cmd_data.get("params", [""])[0]
        print(f"[ASSISTANT] Searching the web for: {query}")
        # In a real implementation, you would add code to perform the search
        return {"query": query, "status": "searched"}
    
    def system_control(self, cmd_data: Dict) -> Dict:
        """Control system functions"""
        action = "shutdown" if "shut" in cmd_data.get("raw_text", "") else "restart"
        print(f"[ASSISTANT] Initiating system {action}...")
        # In a real implementation, you would add code to control the system
        return {"action": action, "status": "initiated"}
    
    # def create_item(self, cmd_data: Dict) -> Dict:
    #     """Create a new item (file, folder, project, etc.)"""
    #     item_type = cmd_data.get("item_type", "")
    #     item_name = cmd_data.get("item_name", "")
    #     location = cmd_data.get("location", "current directory")
        
    #     print(f"[ASSISTANT] Creating {item_type}: {item_name} in {location}")
        
    #     # Normalize location path
    #     if location == "current directory":
    #         location = os.getcwd()
        
    #     # Determine file extension based on item type
    #     extension = ""
    #     if "python" in item_type:
    #         extension = ".py"
    #     elif "javascript" in item_type:
    #         extension = ".js"
    #     elif "html" in item_type:
    #         extension = ".html"
    #     elif "css" in item_type:
    #         extension = ".css"
    #     elif "markdown" in item_type:
    #         extension = ".md"
    #     elif "json" in item_type:
    #         extension = ".json"
    #     elif "yaml" in item_type:
    #         extension = ".yaml"
    #     elif "text" in item_type:
    #         extension = ".txt"
    #     elif "document" in item_type:
    #         extension = ".docx"
    #     elif "

    def create_item(self) -> None: ...
    def find_files(self) -> None: ...

    def control_wifi(self, cmd_data: Dict) -> Dict:
        """Control WiFi connection"""
        action = "connect" if any(x in cmd_data.get("raw_text", "") for x in ["connect", "on"]) else "disconnect"
        print(f"[JARVIS] {action.capitalize()}ing WiFi...")
        # In a real implementation, you would add code to control WiFi
        return {"action": action, "status": "completed"}
    
    def set_timer(self, cmd_data: Dict) -> Dict:
        """Set a timer"""
        params = cmd_data.get("params", ["0", "minute"])
        duration = int(params[0])
        unit = params[1]
        print(f"[JARVIS] Setting timer for {duration} {unit}(s)")
        # In a real implementation, you would add code to set a timer
        return {"duration": duration, "unit": unit, "status": "set"}
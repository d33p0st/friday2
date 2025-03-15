import re
import json
import os
from typing import Dict, List, Tuple, Optional, Callable
from difflib import get_close_matches
import time

class CommandParser:
    def __init__(self, commands_file: str = "commands.json"):
        """
        Initialize the command parser with predefined commands.
        
        Args:
            commands_file: Path to JSON file containing command definitions
        """
        self.commands = self._load_commands(commands_file)
        self.trigger_phrases = ["hey friday", "friday", "jarvis", "hey jarvis"]
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
                "web_search": {
                    "patterns": [
                        r"search\s+(?:for\s+)?(.+)",
                        r"look\s+up\s+(.+)",
                        r"find\s+(.+)"
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
                        r"create\s+(?:a\s+)?(?:new\s+)?(\w+(?:\s+\w+)*)\s+(?:project|file|folder)\s+(?:named|called)?\s+[\"']?([^\"']+)[\"']?",
                        r"make\s+(?:a\s+)?(?:new\s+)?(\w+(?:\s+\w+)*)\s+(?:project|file|folder)(?:\s+named|\s+called)?\s+[\"']?([^\"']+)[\"']?"
                    ],
                    "function": "create_project"
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
        
        Args:
            transcription: The transcribed text from speech recognition
            
        Returns:
            Dictionary containing command info or None if no command detected
        """
        # Normalize text for easier matching
        text = transcription.lower().strip()
        
        # Check if text starts with or contains a trigger phrase
        has_trigger = False
        trigger_pos = len(text)
        for trigger in self.trigger_phrases:
            if text.startswith(trigger):
                text = text[len(trigger):].strip()
                has_trigger = True
                break
            pos = text.find(trigger)
            if pos != -1 and pos < trigger_pos:
                trigger_pos = pos
                has_trigger = True
        
        if has_trigger and trigger_pos < len(text):
            # Extract the part after the trigger phrase if it's in the middle
            if not text and trigger_pos > 0:
                text = text[trigger_pos + len(trigger):].strip()
        
        # If no explicit command structure is found, try to detect the intent
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
                                
                    return result
        
        # If no pattern matched, try to infer the intent
        return self._infer_intent(text)
    
    def _infer_intent(self, text: str) -> Optional[Dict]:
        """Infer the command intent from free-form text"""
        # Simple keyword-based intent detection
        keywords = {
            "open": ["open", "launch", "start", "run"],
            "web_search": ["search", "look up", "find", "google"],
            "system": ["shutdown", "restart", "reboot", "turn off"],
            "create": ["create", "make", "new"],
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
            "create_project": self.create_project,
            "control_wifi": self.control_wifi,
            "set_timer": self.set_timer
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
        print(f"[JARVIS] Opening {target}...")
        # In a real implementation, you would add code to open the app or website
        return {"target": target, "status": "opened"}
    
    def web_search(self, cmd_data: Dict) -> Dict:
        """Perform a web search"""
        query = cmd_data.get("params", [""])[0]
        print(f"[JARVIS] Searching for: {query}")
        # In a real implementation, you would add code to perform the search
        return {"query": query, "status": "searched"}
    
    def system_control(self, cmd_data: Dict) -> Dict:
        """Control system functions"""
        action = "shutdown" if "shut" in cmd_data.get("raw_text", "") else "restart"
        print(f"[JARVIS] Initiating system {action}...")
        # In a real implementation, you would add code to control the system
        return {"action": action, "status": "initiated"}
    
    def create_project(self, cmd_data: Dict) -> Dict:
        """Create a new project or file"""
        project_type = cmd_data.get("params", ["", ""])[0]
        project_name = cmd_data.get("params", ["", ""])[1]
        print(f"[JARVIS] Creating {project_type} project: {project_name}")
        # In a real implementation, you would add code to create the project
        return {"type": project_type, "name": project_name, "status": "created"}
    
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


# Example of integration with speech recognition
def main():
    # Initialize the command system
    parser = CommandParser()
    executor = CommandExecutor(parser)
    
    # Example commands
    test_commands = [
        "Open GitHub",
        "Hey Friday, open Terminal and start a new Python project named AI_Assistant",
        "Search for Python speech recognition libraries",
        "Restart the system",
        "Turn off WiFi for 10 seconds",
        "Set a timer for 30 minutes",
        "Friday, what's the weather like today?",  # Unknown command
        "Create a new Python project called JARVIS",
        "Open VS Code and load the JARVIS project"
    ]
    
    # Process each command
    for cmd in test_commands:
        print(f"\nTesting command: '{cmd}'")
        result = executor.execute(cmd)
        print(f"Result: {'✅' if result['success'] else '❌'} {result['message']}")
        if "result" in result:
            print(f"Details: {result['result']}")
        print("-" * 50)
    
if __name__ == "__main__":
    main()
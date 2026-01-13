"""
Reflection Layer 
"""
import re
import json
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ReflectionLayer:
    """Validate and optimize reflexion """
    
    # validate schema 
    TOOL_SCHEMAS = {
        "search": {
            "required": ["query"],
            "min_query_length": 3,
            "max_query_length": 200
        },
        "scrape": {
            "required": ["url"],
            "validate_url": True
        },
        "sandbox": {
            "required": ["code"],
            "max_code_length": 5000
        },
        "command": {
            "required": ["command"],
            "dangerous_commands": ["rm -rf", "sudo ", "dd ", "> /", ":(){ :|:& };:"]
        },
        "manage_notes": {
            "required": ["action"],
            "valid_actions": ["create", "search", "update", "delete", "categories"]
        },
        "manage_calendar": {
            "required": ["action"],
            "valid_actions": ["add", "list", "remove", "update"]
        },
        "manage_wallet": {
            "required": ["action"],
            "valid_actions": ["balance", "history", "prepare_transfer"]
        },
        "image_search": {
            "required": ["query"],
            "min_query_length": 2
        },
        "video_search": {
            "required": ["query"],
            "min_query_length": 2
        },
        "osint_lookup": {
            "required": ["target", "type"],
            "valid_types": ["username", "domain", "email"]
        },
        "get_weather": {
            "required": ["location"]
        }
    }
    
    @classmethod
    def validate(cls, tool_call: Dict[str, Any], context_history: List[Dict]) -> Dict[str, Any]:
        """
        Valide un tool call complet
        """
        tool_name = tool_call.get("tool")
        
        # verify if the tool exist to prevent token waste
        if not tool_name:
            return {
                "valid": False,
                "reason": "Missing tool name",
                "suggestion": "Specify which tool to use in the format {\"tool\": \"...\", ...}"
            }
        
        schema = cls.TOOL_SCHEMAS.get(tool_name)
        if not schema:
            return {
                "valid": False,
                "reason": f"Unknown tool: {tool_name}",
                "suggestion": f"Available tools: {', '.join(cls.TOOL_SCHEMAS.keys())}"
            }
        
        # verify required params
        for param in schema.get("required", []):
            if param not in tool_call or not tool_call[param]:
                # Special case: manage_notes/wallet fallback already handled in ai_service, 
                # but if it reached here without the param, it's invalid.
                return {
                    "valid": False,
                    "reason": f"Missing required parameter: {param}",
                    "suggestion": f"Add '{param}' to the {tool_name} call"
                }
        
        #specific validation for each tools
        if tool_name == "search":
            query = tool_call.get("query", "")
            min_len = schema["min_query_length"]
            max_len = schema["max_query_length"]
            
            if len(query) < min_len:
                return {
                    "valid": False,
                    "reason": f"Query too short ({len(query)} chars, need {min_len}+)",
                    "suggestion": "Use more specific search terms"
                }
            
            if len(query) > max_len:
                return {
                    "valid": False,
                    "reason": f"Query too long ({len(query)} chars, max {max_len})",
                    "suggestion": "Shorten the query to its essence"
                }
        
        elif tool_name == "scrape":
            url = tool_call.get("url", "")
            if not cls._is_valid_url(url):
                return {
                    "valid": False,
                    "reason": f"Invalid URL format: {url}",
                    "suggestion": "Provide a valid HTTP or HTTPS URL"
                }
        
        elif tool_name == "command":
            command = tool_call.get("command", "")
            dangerous = schema["dangerous_commands"]
            
            if any(cmd in command for cmd in dangerous):
                return {
                    "valid": False,
                    "reason": f"Potentially dangerous command detected: {command}",
                    "suggestion": "Restricted command. Try a different approach."
                }
        
        elif tool_name in ["manage_notes", "manage_wallet", "manage_calendar"]:
            action = tool_call.get("action")
            valid_actions = schema["valid_actions"]
            
            if action not in valid_actions:
                return {
                    "valid": False,
                    "reason": f"Invalid action '{action}' for {tool_name}",
                    "suggestion": f"Use one of: {', '.join(valid_actions)}"
                }
        
        # Verify if its redundant with the context 
        if cls._is_redundant(tool_call, context_history):
            return {
                "valid": False,
                "reason": "Information already available or recently sought in context",
                "suggestion": "Summarize what you already found or try a different search term"
            }
        
        return {"valid": True}
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Valide une URL basique"""
        if not isinstance(url, str): return False
        pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(pattern.match(url))
    
    @staticmethod
    def _is_redundant(tool_call: Dict[str, Any], context_history: List[Dict]) -> bool:
        """
        verify if a message is redundant 
        """
        if tool_call.get("tool") != "search":
            return False
        
        query = tool_call.get("query", "").lower()
        
        # Verify the 5 last messages of the ai (tools outputs)
        for msg in context_history[-8:]:
            content = str(msg.get("content", "")).lower()
            
            # if the query already exactly appears in another [TOOL_EXECUTION] recent
            if f"input: {query}" in content:
                logger.info(f"🔍 Redundant search detected: '{query}'")
                return True
        
        return False

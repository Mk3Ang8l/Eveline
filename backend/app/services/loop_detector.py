"""
Loop Detector - Prevents infinite loops
"""
import json
from collections import deque
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class LoopDetector:
    """Detects 3 types of loops: immediate, cycle, repetition"""
    
    def __init__(self, max_history: int = 10, max_repeats: int = 2):
        self.history = deque(maxlen=max_history)
        self.max_repeats = max_repeats
        self.repeat_counts = {}
        
    def check(self, tool_call: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Checks if a tool call would create a loop
        
        Returns:
            (is_loop: bool, reason: str)
        """
        try:
            payload = json.dumps(tool_call, sort_keys=True)
            
            # Level 1: immediate repetition (A → A)
            if self.history and self.history[-1] == payload:
                logger.warning(f"🔁 Immediate repetition: {tool_call.get('tool')}")
                return (True, "IMMEDIATE_REPEAT")
            
            # Level 2: Short cycle (A → B → A → B)
            if len(self.history) >= 3:
                # Check for A-B-A pattern
                if self.history[-2] == payload:
                    logger.warning(f"🔄 A-B-A cycle detected: {tool_call.get('tool')}")
                    return (True, "SHORT_CYCLE")
            
            if len(self.history) >= 4:
                # Check for A-B-C-A or similar
                if (self.history[-3] == payload or self.history[-4] == payload):
                    logger.warning(f"🔄 Cycle detected in history: {tool_call.get('tool')}")
                    return (True, "CYCLE_DETECTED")
            
            # Level 3: excessive repetition
            self.repeat_counts[payload] = self.repeat_counts.get(payload, 0) + 1
            
            if self.repeat_counts[payload] > self.max_repeats:
                count = self.repeat_counts[payload]
                logger.error(f"❌ Repeated {count} times: {tool_call.get('tool')}")
                return (True, f"REPEATED_{count}_TIMES")
            
            # Add to history if OK
            self.history.append(payload)
            return (False, None)
        except Exception as e:
            logger.error(f"Loop detector error: {e}")
            return (False, None)
    
    def reset(self):
        """Resets for a new conversation"""
        self.history.clear()
        self.repeat_counts.clear()
        logger.info("🔄 Loop detector reset")

"""
Eveline's Memory System
Stores conversation history, user preferences, and learned context
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging
from config import DATA_ROOT

logger = logging.getLogger(__name__)

MEMORY_DIR = DATA_ROOT / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

class MemoryService:
    """
    Three-layer memory system:
    1. Working Memory (current conversation)
    2. Short-term Memory (recent sessions)
    3. Long-term Memory (persistent knowledge)
    """
    
    @staticmethod
    def _get_memory_path(memory_type: str) -> Path:
        """Get path for specific memory file"""
        return MEMORY_DIR / f"{memory_type}.json"
    
    # ==================== WORKING MEMORY ====================
    
    @staticmethod
    def extract_entities(message: str) -> List[str]:
        """
        Extract key entities (topics, names, concepts) from message
        Simple keyword extraction for now
        """
        # Common topics to track
        keywords = {
            'bitcoin', 'crypto', 'python', 'javascript', 'ai', 'ml',
            'vps', 'server', 'docker', 'react', 'api', 'database',
            'trading', 'investment', 'portfolio', 'stock', 'finance',
            'ethereum', 'solana', 'blockchain', 'linux', 'windows', 'macos'
        }
        
        message_lower = message.lower()
        found = [kw for kw in keywords if kw in message_lower]
        return found
    
    # ==================== SHORT-TERM MEMORY ====================
    
    @classmethod
    def save_conversation_snippet(cls, user_msg: str, ai_response: str, entities: List[str]):
        """
        Save important conversation moments
        """
        memory_path = cls._get_memory_path("short_term")
        
        # Load existing
        try:
            if memory_path.exists():
                with open(memory_path, 'r', encoding='utf-8') as f:
                    memories = json.load(f)
            else:
                memories = []
        except Exception:
            memories = []
        
        # Add new memory
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_msg[:200],  # Truncate for storage
            "assistant": ai_response[:500],
            "entities": entities,
            "date_readable": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        memories.append(memory_entry)
        
        # Keep only last 50 conversations
        memories = memories[-50:]
        
        # Save
        try:
            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(memories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save short-term memory: {e}")
    
    @classmethod
    def get_recent_topics(cls, limit: int = 10) -> List[str]:
        """Get topics discussed recently"""
        memory_path = cls._get_memory_path("short_term")
        
        if not memory_path.exists():
            return []
        
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                memories = json.load(f)
        except Exception:
            return []
        
        # Collect all entities from recent conversations
        all_entities = []
        for mem in memories[-limit:]:
            all_entities.extend(mem.get("entities", []))
        
        # Count frequency
        from collections import Counter
        entity_counts = Counter(all_entities)
        
        # Return top topics
        return [entity for entity, count in entity_counts.most_common(5)]
    
    @classmethod
    def search_memory(cls, query: str, limit: int = 3) -> List[Dict]:
        """
        Search through conversation history
        """
        memory_path = cls._get_memory_path("short_term")
        
        if not memory_path.exists():
            return []
        
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                memories = json.load(f)
        except Exception:
            return []
        
        query_lower = query.lower()
        
        # Simple keyword match
        relevant = []
        for mem in reversed(memories):  # Most recent first
            text = f"{mem['user']} {mem['assistant']}".lower()
            if query_lower in text or any(entity in query_lower for entity in mem.get('entities', [])):
                relevant.append(mem)
                if len(relevant) >= limit:
                    break
        
        return relevant
    
    # ==================== LONG-TERM MEMORY (Preferences) ====================
    
    @classmethod
    def save_preference(cls, key: str, value: str):
        """
        Save user preferences
        Examples: preferred_detail_level, interests, language_preference
        """
        prefs_path = cls._get_memory_path("preferences")
        
        # Load existing
        try:
            if prefs_path.exists():
                with open(prefs_path, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
            else:
                prefs = {}
        except Exception:
            prefs = {}
        
        prefs[key] = {
            "value": value,
            "updated": datetime.now().isoformat()
        }
        
        # Save
        try:
            with open(prefs_path, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    @classmethod
    def get_preference(cls, key: str) -> Optional[str]:
        """Get a preference value"""
        prefs_path = cls._get_memory_path("preferences")
        
        if not prefs_path.exists():
            return None
        
        try:
            with open(prefs_path, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
            return prefs.get(key, {}).get("value")
        except Exception:
            return None
    
    @classmethod
    def get_all_preferences(cls) -> Dict:
        """Get all preferences"""
        prefs_path = cls._get_memory_path("preferences")
        
        if not prefs_path.exists():
            return {}
        
        try:
            with open(prefs_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    # ==================== LEARNED FACTS ====================
    
    @classmethod
    def save_learned_fact(cls, topic: str, fact: str, source: str = "user"):
        """
        Save facts learned during conversations
        """
        facts_path = cls._get_memory_path("learned_facts")
        
        # Load existing
        try:
            if facts_path.exists():
                with open(facts_path, 'r', encoding='utf-8') as f:
                    facts = json.load(f)
            else:
                facts = {}
        except Exception:
            facts = {}
        
        if topic not in facts:
            facts[topic] = []
        
        fact_entry = {
            "fact": fact,
            "source": source,
            "learned_at": datetime.now().isoformat()
        }
        
        # Avoid duplicates
        if not any(f['fact'] == fact for f in facts[topic]):
            facts[topic].append(fact_entry)
        
        # Save
        try:
            with open(facts_path, 'w', encoding='utf-8') as f:
                json.dump(facts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save learned fact: {e}")
    
    @classmethod
    def get_facts_about(cls, topic: str) -> List[str]:
        """Get learned facts about a topic"""
        facts_path = cls._get_memory_path("learned_facts")
        
        if not facts_path.exists():
            return []
        
        try:
            with open(facts_path, 'r', encoding='utf-8') as f:
                facts = json.load(f)
            topic_facts = facts.get(topic, [])
            return [f['fact'] for f in topic_facts]
        except Exception:
            return []
    
    # ==================== CONTEXT BUILDER ====================
    
    @classmethod
    def build_context_summary(cls) -> str:
        """
        Build a summary of Eveline's memory for the system prompt
        """
        summary_parts = []
        
        # Recent topics
        recent_topics = cls.get_recent_topics()
        if recent_topics:
            summary_parts.append(f"Recent topics discussed: {', '.join(recent_topics)}")
        
        # Preferences
        prefs = cls.get_all_preferences()
        if prefs:
            pref_summary = ", ".join([f"{k}: {v['value']}" for k, v in prefs.items()])
            summary_parts.append(f"User preferences: {pref_summary}")
        
        # Return formatted summary
        if summary_parts:
            return "MEMORY CONTEXT:\n" + "\n".join(f"- {part}" for part in summary_parts)
        else:
            return "MEMORY CONTEXT: New conversation, no prior context."

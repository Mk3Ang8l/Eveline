"""
Context Manager - Intelligent context window management
"""
import tiktoken
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ContextManager:
    """Dynamically manages context to stay within token limits"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", max_tokens: int = 30000):
        """
        Args:
            model: Model for the tokenizer (Mistral/OpenAI compatible)
            max_tokens: Token limit for the context (Mistral Small default)
        """
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base") # Standard for most modern LLMs
        except Exception as e:
            logger.warning(f"Could not load tiktoken encoder: {e}. Fallback enabled.")
            self.encoder = None
        
        self.max_tokens = max_tokens
        logger.info(f"📊 Context Manager initialized (max: {max_tokens} tokens)")
    
    def build_optimized_context(
        self,
        system_prompt: str,
        user_query: str,
        history: List[Dict[str, Any]],
        system_info: Dict[str, Any] = None
    ) -> List[Dict[str, str]]:
        """
        Builds an optimized context
        """
        context = []
        token_count = 0
        
        # 1. System prompt (absolute priority)
        system_msg = {"role": "system", "content": system_prompt}
        system_tokens = self._count_tokens(system_msg["content"])
        context.append(system_msg)
        token_count += system_tokens
        
        # 2. Add System Info (Wallet state, etc.)
        if system_info:
            info_content = "SYSTEM_STATE:\n" + "\n".join([f"{k}: {v}" for k, v in system_info.items()])
            info_msg = {"role": "system", "content": info_content}
            info_tokens = self._count_tokens(info_content)
            
            # Use small budget for system info
            if token_count + info_tokens < self.max_tokens * 0.2:
                context.append(info_msg)
                token_count += info_tokens
        
        # 3. User query (high priority)
        user_tokens = self._count_tokens(user_query)
        
        # 4. History (LIFO)
        # Allocate 60% of remaining tokens to history
        remaining_budget = self.max_tokens - token_count - user_tokens - 200 # 200 buffer
        if remaining_budget < 0:
            remaining_budget = 500 # minimum safety
            
        added_history = []
        history_tokens = 0
        
        # Filter and prioritize history
        prioritized_history = [self._format_message(m) for m in history if self._format_message(m)]
        
        for msg in reversed(prioritized_history):
            msg_tokens = self._count_tokens(msg["content"])
            if history_tokens + msg_tokens > remaining_budget:
                break
            added_history.insert(0, msg)
            history_tokens += msg_tokens
            
        # 5. Summary of very old history if there's space left
        if len(prioritized_history) > len(added_history) and (remaining_budget - history_tokens) > 300:
            old_history = prioritized_history[:-len(added_history)]
            summary_text = self._summarize_old_messages(old_history)
            summary_msg = {"role": "system", "content": f"PREVIOUS_CONVERSATION_SUMMARY: {summary_text}"}
            context.insert(1, summary_msg)
            token_count += self._count_tokens(summary_text)

        # Final Assembly
        context.extend(added_history)
        context.append({"role": "user", "content": user_query})
        
        logger.info(f"✅ Context built: {len(context)} msgs, ~{token_count + user_tokens} tokens")
        return context
    
    def _count_tokens(self, text: str) -> int:
        if not self.encoder:
            return len(text) // 4 # heuristic
        return len(self.encoder.encode(text))
    
    def _format_message(self, msg: Dict[str, Any]) -> Dict[str, str]:
        """Convert system history format to OpenAI/Mistral format"""
        m_type = msg.get("type")
        text = msg.get("text", "")
        
        # DIRECT SUPPORT for already formatted messages (from DB or clean source)
        if "role" in msg and "content" in msg:
             return {"role": msg["role"], "content": msg["content"]}

        if m_type == "input":
            return {"role": "user", "content": str(text).replace("> ", "")}
        elif m_type == "output":
            return {"role": "assistant", "content": str(text)}
        elif m_type == "agent-step":
            if isinstance(text, dict):
                tool = text.get("tool", "cmd")
                inp = text.get("input", "")
                out = str(text.get("output", ""))[:150] # Truncate large outputs in context
                return {"role": "assistant", "content": f"[TOOL] {tool}({inp}) -> {out}"}
        return None

    def _summarize_old_messages(self, old_msgs: List[Dict]) -> str:
        """Simple heuristic summary"""
        topics = set()
        for m in old_msgs:
            content = m["content"].lower()
            for kw in ["bitcoin", "crypto", "note", "wallet", "search", "python", "fix"]:
                if kw in content: topics.add(kw)
        
        if topics:
            return f"Discussed topics like {', '.join(list(topics)[:5])}."
        return "Earlier context involved general system interactions."

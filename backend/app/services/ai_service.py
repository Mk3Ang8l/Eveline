import httpx
import logging
import json
import sys
import os
import time
import re
from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()
logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

from .loop_detector import LoopDetector
from .reflection_layer import ReflectionLayer
from .context_manager import ContextManager
try:
    from .vector_memory import VectorMemory
    VECTOR_MEMORY_AVAILABLE = True
except ImportError:
    VECTOR_MEMORY_AVAILABLE = False
    logger.warning("⚠️ Vector Memory not available (install sentence-transformers + faiss-cpu)")

class AIService:
    # Instances globales (singleton pattern)
    _vector_memory = None
    _context_manager = None
    
    @staticmethod
    def get_vector_memory():
        """Lazy initialization de la mémoire vectorielle"""
        if AIService._vector_memory is None and VECTOR_MEMORY_AVAILABLE:
            AIService._vector_memory = VectorMemory()
        return AIService._vector_memory
    
    @staticmethod
    def get_context_manager():
        """Lazy initialization du gestionnaire de contexte"""
        if AIService._context_manager is None:
            AIService._context_manager = ContextManager(max_tokens=30000)
        return AIService._context_manager
    
    @staticmethod
    async def get_chat_response_stream(message: str, session_id: str, db: Session, context: list = None, is_discord: bool = False):
        import re
        import time
        from .scraping_service import ScrapingService
        from .search_service import SearchService
        from .sandbox_service import SandboxService
        from .account_service import AccountService
        from .memory_service import MemoryService
        from .calendar_service import CalendarService
        from .crypto_service import CryptoService
        from .realtime_service import RealtimeService
        from .image_search_service import ImageSearchService
        from .video_search_service import VideoSearchService
        from .osint_service import OSINTService
        from .time_service import TimeService
        from .weather_service import WeatherService
        from .notes_service import NotesService
        from .vision_service import VisionService
        from ..schemas.notes import NoteCreate, NoteUpdate, NoteResponse
        from ..schemas.notes import NoteCreate, NoteUpdate, NoteResponse
        from ..core.database import SessionLocal
        from ..services.history_service import HistoryService
        from sqlalchemy.orm import Session
        
        start_time = time.time()
        TIMEOUT_SECONDS = 60 # Extended for complex reasoning
        
        # 0. PERSISTENCE LAYER - SAVE USER MESSAGE
        if session_id and db:
             try:
                 HistoryService.add_message(db, session_id, "user", message)
             except Exception as e:
                 logger.error(f"Failed to save user message: {e}")

        # 1. INITIALISER LES SYSTÈMES INTELLIGENTS
        loop_detector = LoopDetector(max_history=12, max_repeats=2)
        context_manager = AIService.get_context_manager()
        vector_memory = AIService.get_vector_memory()
        
        # 2. RECHERCHE SÉMANTIQUE DANS LA MÉMOIRE
        memory_context = ""
        if vector_memory:
            relevant_memories = vector_memory.search(message, top_k=3, min_score=0.45)
            if relevant_memories:
                memory_texts = [f"- {mem['text'][:150]}" for mem in relevant_memories]
                memory_context = f"\nRELEVANT_MEMORIES_FROM_PAST:\n" + "\n".join(memory_texts)
                logger.info(f"🧠 Found {len(relevant_memories)} relevant memories")
        
        # 3. GATHER SYSTEM STATS
        memory_summary = MemoryService.build_context_summary()
        current_entities = MemoryService.extract_entities(message)
        
        system_stats = {}
        connected_wallet = "NONE"
        
        # Use provided context only for system state extraction (legacy frontend context)
        if context:
            for msg in context:
                content = str(msg.get("content", "") or msg.get("text", ""))
                if "CONNECTED_WALLET:" in content:
                    connected_wallet = content.split("CONNECTED_WALLET:")[1].strip()
                    break

        try:
            sessions = AccountService.list_accounts()
            system_stats = {
                "active_sessions": sessions,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "recent_topics": MemoryService.get_recent_topics(limit=5),
                "memory_summary": memory_summary,
                "connected_wallet": connected_wallet
            }
        except Exception as e:
            logger.warning(f"Warmup pre-fetch failed: {e}")
            system_stats = {"error": "Stats incomplete", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
        
        yield json.dumps({"type": "info", "content": "Eveline initializing context & neural memory..."}) + "\n"

        if not MISTRAL_API_KEY:
             yield json.dumps({"type": "error", "content": "MISTRAL_API_KEY is missing"}) + "\n"
             return

        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # 4. ADVANCED SYSTEM PROMPT
        system_prompt_content = (
            "You are Eveline, a personal AI assistant. You help with EVERYDAY tasks.\n"
            "Date: {{currentDateTime}}.\n\n"
            "<directives>\n"
            "- LANGUAGE: You MUST answer in FRENCH (Français) unless explicitly asked otherwise.\n"
            "- BE USEFUL: Help with daily tasks: reminders, calculations, research, planning, organization.\n"
            "- SPEED AND ACTION: Use tools immediately. Do not announce them.\n"
            "- DIRECT RESPONSES: Be concise and helpful. No fluff.\n"
            "- PERSISTENCE: If research is needed, use search/scrape as a chain.\n"
            "- NO CHATTER: Do not say 'I will search...'. Just output the JSON Action.\n"
            "- PROACTIVE: Suggest improvements, remind about upcoming events, be anticipatory.\n"
            "- LEARN FROM COMMANDS: Remember command outputs for future reference.\n"
            "</directives>\n\n"
            
            "<everyday_capabilities>\n"
            "You can help with:\n"
            "- Quick calculations (use sandbox for math)\n"
            "- Setting reminders and calendar events\n"
            "- Research and web lookups\n"
            "- File and system management (via command tool)\n"
            "- Note taking and organization\n"
            "- Weather and time information\n"
            "- Crypto portfolio monitoring\n"
            "- Image analysis and search\n"
            "- Learning and remembering Linux commands\n"
            "</everyday_capabilities>\n\n"
        )
        
        if memory_context:
            system_prompt_content += memory_context + "\n\n"

        if is_discord:
            system_prompt_content += "\n<discord_mode>You are on Discord. Be cool, use emojis, keep it crisp.</discord_mode>\n"

        system_prompt_content += (
            "<tools_library>\n"
            "Format: {\"tool\": \"name\", \"parameter_key\": \"value\", \"private\": boolean} \n"
            "- Add \"private\": true to ANY tool call if you want to execute it without showing the output to the user.\n"
            "- Root level parameters only, NO nesting under 'param'.\n\n"
            "EVERYDAY TOOLS:\n"
            "1. search: {\"query\": \"...\"} - Web search\n"
            "2. scrape: {\"url\": \"...\"} - Extract text from URL\n"
            "3. sandbox: {\"code\": \"...\"} - Execute Python (calculations, scripts). Use print() for output.\n"
            "4. command: {\"command\": \"...\"} - Shell/Linux commands. LEARN from results.\n"
            "5. manage_notes: {\"action\": \"create|search|update|delete\", \"title\": \"...\", \"content\": \"...\", \"category\": \"General\"}\n"
            "6. manage_calendar: {\"action\": \"add|list|remove\", \"title\": \"...\", \"start\": \"YYYY-MM-DD HH:MM\", \"description\": \"...\"}\n"
            "7. manage_wallet: {\"action\": \"balance|history|prepare_transfer\", ...}\n"
            "8. get_time: {} - Current time\n"
            "9. get_weather: {\"city\": \"...\"} - Weather info\n"
            "10. image_search: {\"query\": \"...\"} - Find images\n"
            "11. vision_analyze: {\"image_path\": \"...\", \"image_url\": \"...\", \"prompt\": \"...\"} - Analyze images\n"
            "12. osint_lookup: {\"target\": \"...\", \"type\": \"username|domain|email\"}\n"
            "</tools_library>\n\n"
        )
        
        
        # 5. CONTEXT MANAGEMENT (TikToken Optimized)
        
        # Build history from DB if available
        history_for_context = []
        if session_id and db:
             try:
                 # Fetch last 15 messages (Chronological)
                 db_history = HistoryService.get_session_history(db, session_id, limit=15)
                 # Format and EXCLUDE the last message (which is the current user message we just added)
                 # HistoryService.get_session_history returns chronological [oldest ... newest]
                 if db_history and db_history[-1].role == "user" and db_history[-1].content == message:
                      db_history = db_history[:-1]
                 
                 history_for_context = [{"role": m.role, "content": m.content} for m in db_history]
             except Exception as e:
                 logger.error(f"Failed to fetch history: {e}")
                 history_for_context = context if context else [] # Fallback
        else:
             history_for_context = context if context else []

        current_context = context_manager.build_optimized_context(
            system_prompt=system_prompt_content,
            user_query=message,
            history=history_for_context,
            system_info=system_stats
        )
        
        current_context = AIService._clean_context(current_context)
        
        last_tool_call = None
        search_count = 0
        max_steps = 10
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                for step_i in range(max_steps):
                    if time.time() - start_time > TIMEOUT_SECONDS:
                         yield json.dumps({"type": "final", "content": "⏱️ Timeout de recherche. Voici ma synthèse actuelle."}) + "\n"
                         return

                    payload = {
                        "model": "mistral-large-latest",
                        "messages": current_context,
                        "stream": False,
                        "temperature": 0.1,
                        "max_tokens": 2000
                    }
                    
                    try:
                        response = await client.post(MISTRAL_API_URL, headers=headers, json=payload)
                        if response.status_code != 200:
                            yield json.dumps({"type": "error", "content": f"🌐 API Error {response.status_code}"}) + "\n"
                            return
                        data = response.json()
                        ai_content = data["choices"][0]["message"]["content"]
                    except Exception as e:
                        yield json.dumps({"type": "error", "content": f"🌐 Connection Error: {str(e)}"}) + "\n"
                        return
                    
                    yield json.dumps({"type": "thought", "content": ai_content}) + "\n"
                    
                    # 6. TOOL EXTRACTION & VALIDATION
                    tool_call = None
                    try:
                        json_match = re.search(r'(\{.*?\})', ai_content, re.DOTALL)
                        if json_match:
                            tool_call = json.loads(json_match.group(1))
                            
                            # Fallback auto-tool name
                            if "tool" not in tool_call and "action" in tool_call:
                                if tool_call["action"] in ["create", "update", "delete", "search", "categories"]:
                                    tool_call["tool"] = "manage_notes"
                                elif tool_call["action"] in ["balance", "history", "prepare_transfer"]:
                                    tool_call["tool"] = "manage_wallet"
                    except Exception:
                        pass 
                    
                    # 7. ANTI-CHATTER REFLECTION
                    if not tool_call:
                        lower_c = ai_content.lower()
                        intents = ["je vais", "i will", "recherche", "let me", "checking"]
                        hints = ["search", "recherche", "note", "scrape", "image", "wallet"]
                        if any(i in lower_c for i in intents) and any(h in lower_c for h in hints) and len(ai_content) < 250:
                            current_context.append({"role": "assistant", "content": ai_content})
                            current_context.append({"role": "user", "content": "SYSTEM ALERT: You announced an action but forgot the JSON tool call. DO NOT TALK. USE THE TOOL NOW."})
                            continue
 
                    if tool_call and "tool" in tool_call:
                        tool_name = tool_call.get("tool")
                        display_input = str(tool_call.get("query") or tool_call.get("url") or tool_call.get("action") or tool_call.get("command") or "Processing...")
                        
                        # 8. LOOP & VALIDATION LAYERS
                        is_loop, reason = loop_detector.check(tool_call)
                        if is_loop:
                            current_context.append({"role": "assistant", "content": ai_content})
                            current_context.append({"role": "user", "content": f"SYSTEM: Loop detected ({reason}). Provide final answer with current info."})
                            continue

                        validation = ReflectionLayer.validate(tool_call, current_context)
                        if not validation["valid"]:
                            current_context.append({"role": "assistant", "content": ai_content})
                            current_context.append({"role": "user", "content": f"VALIDATION ERROR: {validation['reason']}. {validation.get('suggestion', '')}"})
                            continue

                        # Execute Tool
                        yield json.dumps({"type": "step_start", "tool": tool_name.upper(), "input": display_input}) + "\n"
                        
                        execution_result = ""
                        status = "success"
                        
                        try:
                            if tool_name == "search":
                                results = SearchService.search(tool_call.get("query"))
                                execution_result = json.dumps(results, indent=2, ensure_ascii=False)
                                search_count += 1
                            elif tool_name == "scrape":
                                execution_result = await ScrapingService.scrape_url(tool_call.get("url"))
                            elif tool_name == "sandbox":
                                execution_result = SandboxService.execute_code(tool_call.get("code"))
                            elif tool_name == "command":
                                cmd = tool_call.get("command")
                                execution_result = SandboxService.execute_command(cmd)
                                
                                # LINUX COMMAND LEARNING: Store in vector memory
                                if VECTOR_MEMORY_AVAILABLE and execution_result:
                                    memory_text = f"COMMAND: {cmd}\nRESULT: {execution_result[:500]}"
                                    AIService.get_vector_memory().add_memory(
                                        memory_text,
                                        metadata={"type": "linux_command", "command": cmd}
                                    )
                            elif tool_name == "manage_notes":
                                action = tool_call.get("action")
                                with SessionLocal() as db:
                                    if action == "create":
                                        note_data = NoteCreate(
                                            title=tool_call.get("title", "Sans titre"),
                                            content=tool_call.get("content", ""),
                                            category=tool_call.get("category", "General"),
                                            tags=tool_call.get("tags", "")
                                        )
                                        execution_result = json.dumps(NoteResponse.model_validate(NotesService.create_note(db, note_data)).model_dump(), default=str)
                                    elif action == "search":
                                        results = NotesService.get_all_notes(db, search=tool_call.get("query"))
                                        execution_result = json.dumps([NoteResponse.model_validate(n).model_dump() for n in results], default=str)
                                    elif action == "update":
                                        update_data = NoteUpdate(
                                            content=tool_call.get("content"),
                                            title=tool_call.get("title")
                                        )
                                        updated = NotesService.update_note(db, int(tool_call.get("id")), update_data)
                                        execution_result = json.dumps(NoteResponse.model_validate(updated).model_dump(), default=str) if updated else "Note not found"
                                    elif action == "delete":
                                        success = NotesService.delete_note(db, int(tool_call.get("id")))
                                        execution_result = json.dumps({"status": "deleted" if success else "failed"})
                                    elif action == "categories":
                                        execution_result = json.dumps(NotesService.get_categories(db))
                            elif tool_name == "manage_wallet":
                                action = tool_call.get("action")
                                if action == "balance":
                                    execution_result = json.dumps(await CryptoService.get_balance(tool_call.get("address")))
                                elif action == "history":
                                    execution_result = json.dumps(await CryptoService.get_transaction_history(tool_call.get("address")))
                                elif action == "prepare_transfer":
                                    execution_result = json.dumps(await CryptoService.prepare_transfer(
                                        to=tool_call.get("to"),
                                        amount=tool_call.get("amount")
                                    ))
                            elif tool_name == "manage_calendar":
                                action = tool_call.get("action")
                                if action == "list":
                                    execution_result = json.dumps(CalendarService.get_events())
                                elif action == "add":
                                    execution_result = json.dumps(CalendarService.add_event(
                                        title=tool_call.get("title"),
                                        start=tool_call.get("start"),
                                        end=tool_call.get("end")
                                    ))
                            elif tool_name == "image_search":
                                results = await ImageSearchService.search_images(tool_call.get("query"))
                                execution_result = json.dumps(results)
                            elif tool_name == "vision_analyze":
                                description = await VisionService.analyze_image(
                                    image_path=tool_call.get("image_path"),
                                    image_url=tool_call.get("image_url"),
                                    prompt=tool_call.get("prompt", "Describe this image in detail.")
                                )
                                execution_result = description
                                
                                # Store in VectorMemory (RAG)
                                if VECTOR_MEMORY_AVAILABLE:
                                    summary = f"Visual Analysis: {description[:100]}..."
                                    AIService.get_vector_memory().add_memory(
                                        content=f"IMAGE_MEMORY: {description}",
                                        metadata={"type": "vision", "path": tool_call.get("image_path")}
                                    )
                            elif tool_name == "osint_lookup":
                                target = tool_call.get("target")
                                if tool_call.get("type") == "username":
                                    results = await OSINTService.check_username(target)
                                else:
                                    results = await OSINTService.domain_lookup(target)
                                execution_result = json.dumps(results)
                            elif tool_name == "monitor_live_feed":
                                execution_result = RealtimeService.get_recent_events()
                            elif tool_name == "get_time":
                                execution_result = time.strftime("%Y-%m-%d %H:%M:%S")
                            elif tool_name == "get_weather":
                                result = await WeatherService.get_weather(tool_call.get("city"))
                                execution_result = json.dumps(result)
                            else:
                                execution_result = f"Tool {tool_name} not implemented yet."
                                status = "error"
                        except Exception as e:
                            logger.error(f"Tool Error: {e}")
                            execution_result = f"[TOOL_ERROR] Execution Failed: {str(e)}. Please analyze this error and retry or adapt your plan."
                            status = "error"
                        finally:
                            yield json.dumps({
                                "type": "step_end", 
                                "tool": tool_name.upper(), 
                                "input": display_input, 
                                "output": execution_result, 
                                "status": status
                            }) + "\n"

                        # Push results to context
                        current_context.append({"role": "assistant", "content": ai_content})
                        current_context.append({"role": "user", "content": f"OBSERVATION: {AIService._clean_result_for_ai(execution_result)}"})
                        continue
                    else:
                        # 9. FINAL ANSWER & MEMORY STORAGE
                        final_response = ai_content
                        if "Final Answer:" in ai_content:
                            final_response = ai_content.split("Final Answer:")[-1].strip()
                        
                        # Cleanup Thought prefix from final answer if needed
                        final_response = re.sub(r'(?i)^Thought:.*?\n', '', final_response).strip()
                        
                        # Semantic storage
                        if vector_memory:
                            memory_text = f"User asked: {message}\nEveline answered: {final_response[:250]}"
                            vector_memory.add_memory(memory_text, {"entities": current_entities})

                        MemoryService.save_conversation_snippet(message, final_response, current_entities)
                        
                        # 10. PERSISTENCE - SAVE ASSISTANT RESPONSE
                        if session_id and db:
                            try:
                                HistoryService.add_message(db, session_id, "assistant", final_response)
                            except Exception as e:
                                logger.error(f"Failed to save assistant response: {e}")

                        yield json.dumps({"type": "final", "content": final_response}) + "\n"
                        return

        except Exception as e:
            logger.error(f"ReAct Logic Error: {e}")
            yield json.dumps({"type": "error", "content": f"SYSTEM_ERROR: {str(e)}"}) + "\n"

    @staticmethod
    def _clean_context(messages: list) -> list:
        if not messages: return []
        cleaned = []
        for msg in messages:
            if not msg.get("content"): continue
            if not cleaned:
                cleaned.append(msg)
                continue
            last = cleaned[-1]
            if last["role"] == msg["role"]:
                last["content"] = last["content"] + "\n\n" + msg["content"]
            else:
                cleaned.append(msg)
        return cleaned

    @staticmethod
    def _clean_result_for_ai(result: str) -> str:
        if not result or not isinstance(result, str): return str(result)
        # Truncate image data or massive results
        data_uri_pattern = r'data:image\/[a-zA-Z]*;base64,[a-zA-Z0-9+/]*={0,2}'
        cleaned = re.sub(data_uri_pattern, '[B64_IMAGE_DATA]', result)
        if len(cleaned) > 12000:
            return cleaned[:12000] + "... [TRUNCATED]"
        return cleaned

    @staticmethod
    async def analyze_content(content: str, task: str):
        return {"response": "Disabled for stability"}

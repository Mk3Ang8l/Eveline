"""
Sandbox Service - Code and Command Execution
Provides Python code execution and shell command capabilities for Eveline.
"""

import subprocess
import logging
import os
import sys
from typing import Dict, Any, Generator

logger = logging.getLogger(__name__)


class SandboxService:
    """
    Sandbox Service for direct execution of code and commands.
    Allows Eveline to interact with the environment securely.
    """
    
    WORKING_DIR = "/app/data/sandbox"
    
    @classmethod
    def _ensure_working_dir(cls):
        """Ensure the working directory exists"""
        if not os.path.exists(cls.WORKING_DIR):
            os.makedirs(cls.WORKING_DIR, exist_ok=True)

    @classmethod
    def execute_code(cls, code: str) -> str:
        """Execute Python code in a subprocess and return output"""
        cls._ensure_working_dir()
        script_path = os.path.join(cls.WORKING_DIR, "temp_script.py")
        
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cls.WORKING_DIR
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            
            if result.returncode != 0:
                return f"EXECUTION ERROR (Code {result.returncode}):\n{output}"
            
            return output if output.strip() else "Success (No output)"
            
        except subprocess.TimeoutExpired:
            return "ERROR: Execution timed out (30s limit)"
        except Exception as e:
            return f"SANDBOX EXCEPTION: {str(e)}"
        finally:
            if os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except:
                    pass

    @classmethod
    def execute_command(cls, command: str) -> str:
        """Execute shell command and return complete output"""
        cls._ensure_working_dir()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=cls.WORKING_DIR
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
                
            if result.returncode != 0:
                return f"COMMAND ERROR (Code {result.returncode}):\n{output}"
                
            return output if output.strip() else "Command executed successfully."
            
        except subprocess.TimeoutExpired:
            return "ERROR: Command timed out (60s limit)"
        except Exception as e:
            return f"COMMAND EXCEPTION: {str(e)}"

    @classmethod
    def execute_command_stream(cls, command: str) -> Generator[str, None, None]:
        """
        Execute shell command with real-time streaming output.
        Yields output line by line as it becomes available.
        """
        cls._ensure_working_dir()
        
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=cls.WORKING_DIR
            )
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    yield line.rstrip('\n')
            
            process.stdout.close()
            return_code = process.wait(timeout=60)
            
            if return_code != 0:
                yield f"[EXIT CODE: {return_code}]"
                
        except subprocess.TimeoutExpired:
            process.kill()
            yield "[ERROR: Command timed out (60s limit)]"
        except Exception as e:
            yield f"[STREAM ERROR: {str(e)}]"

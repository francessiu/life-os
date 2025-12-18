import docker
import tarfile
import io
import asyncio
from typing import Optional

class SandboxService:
    def __init__(self):
        try:
            self.client = docker.from_env()
            # Ensure the image exists (Pulling python:3.9-slim)
            # In production, build a custom image with pandas/numpy pre-installed.
            print("🐳 Initializing Sandbox: Checking for python:3.9-slim image...")
            try:
                self.client.images.get("python:3.9-slim")
            except docker.errors.ImageNotFound:
                print("   ↳ Pulling image (this may take a minute)...")
                self.client.images.pull("python:3.9-slim")
        except Exception as e:
            print(f"❌ Docker not available. Sandbox disabled. Error: {e}")
            self.client = None

    async def execute_python(self, code: str) -> str:
        """Runs Python code in an isolated container."""
        if not self.client:
            return "Error: Sandbox environment is not available."

        # Wrap code to print last expression if not printed (REPL-like behavior)
        # Simple wrapper to catch errors
        wrapped_code = f"""
                        try:
                        {self._indent_code(code)}
                        except Exception as e:
                            print(f"Runtime Error: {{e}}")
                        """
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_in_container, wrapped_code)

    def _indent_code(self, code: str) -> str:
        """Indents code block for the wrapper function."""
        return "\n".join(["    " + line for line in code.split("\n")])

    def _run_in_container(self, code: str) -> str:
        container = None
        try:
            # 1. Create Container
            container = self.client.containers.run(
                "python:3.9-slim",
                command="python -c 'import sys; exec(sys.stdin.read())'",
                detach=True,
                stdin_open=True,
                network_disabled=True, # Network disabled for security (prevent downloading malware)
                mem_limit="128m" # Memory limit 128MB
            )

            # 2. Inject Code via Stdin
            # Interact with the socket directly or use the simple .exec_run API
            # For simplicity with 'python -c', passing via exec_run is cleaner, but stdin is more robust for multi-line.
            # Simpler approach: Write file then run.
            
            # Prepare file stream
            encoded_code = code.encode('utf-8')
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tar_info = tarfile.TarInfo(name='script.py')
                tar_info.size = len(encoded_code)
                tar.addfile(tar_info, io.BytesIO(encoded_code))
            tar_stream.seek(0)

            # Copy file to container
            container.put_archive("/", tar_stream)

            # 3. Execute
            exit_code, output = container.exec_run("python /script.py")
            
            return output.decode('utf-8').strip()

        except Exception as e:
            return f"Sandbox Error: {str(e)}"
        
        finally:
            # 4. Cleanup
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass

# Singleton
sandbox = SandboxService()
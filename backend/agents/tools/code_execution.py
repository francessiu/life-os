from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from backend.services.sandbox_service import sandbox

class CodeInput(BaseModel):
    code: str = Field(description="The pure python code to execute.")

class PythonSandboxTool(BaseTool):
    name = "python_interpreter"
    description = """
    Useful for mathematics, data analysis, or complex logic. 
    Input should be valid Python code. 
    The environment is sandboxed: no internet, limited libraries (standard lib only unless configured).
    """
    args_schema: Type[BaseModel] = CodeInput

    def _run(self, code: str) -> str:
        # Need to run the async sandbox method in a sync context for LangChain _run or use _arun for async
        raise NotImplementedError("Use _arun for async execution")

    async def _arun(self, code: str) -> str:
        print(f"🐍 Executing Code in Sandbox...")
        result = await sandbox.execute_python(code)
        return f"Output:\n{result}"
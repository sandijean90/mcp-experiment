# Copyright 2025 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool as MCPToolInfo
from pydantic import BaseModel

from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter
from beeai_framework.logger import Logger
from beeai_framework.tools import Tool
from beeai_framework.tools.tool import JSONToolOutput, ToolOutput, ToolRunOptions
from beeai_framework.utils.models import JSONSchemaModel
from beeai_framework.utils.strings import to_safe_word

logger = Logger(__name__)


class MCPTool(Tool[BaseModel, ToolRunOptions, ToolOutput]):
    """Tool implementation for Model Context Protocol."""

    def __init__(self, server_params: StdioServerParameters, tool: MCPToolInfo, **options: int) -> None:
        """Initialize MCPTool with client and tool configuration."""
        super().__init__(options)
        self._server_params = server_params
        self._tool = tool

    @property
    def name(self) -> str:
        return self._tool.name

    @property
    def description(self) -> str:
        return self._tool.description or "No available description, use the tool based on its name and schema."

    @property
    def input_schema(self) -> type[BaseModel]:
        return JSONSchemaModel.create(self.name, self._tool.inputSchema)

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "mcp", to_safe_word(self._tool.name)],
            creator=self,
        )

    async def _run(self, input_data: Any, options: ToolRunOptions | None, context: RunContext) -> JSONToolOutput:
        """Execute the tool with given input."""
        logger.debug(f"Executing tool {self._tool.name} with input: {input_data}")
        async with stdio_client(self._server_params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name=self._tool.name, arguments=input_data.model_dump())
            logger.debug(f"Tool result: {result}")
            return JSONToolOutput(result.content)

    @classmethod
    async def from_client(cls, client: ClientSession, server_params: StdioServerParameters) -> list["MCPTool"]:
        tools_result = await client.list_tools()
        return [MCPTool(server_params, tool) for tool in tools_result.tools]

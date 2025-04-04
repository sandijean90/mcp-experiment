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

import asyncio
import random
import string
from collections.abc import Awaitable, Callable
from inspect import isfunction
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, InstanceOf

from beeai_framework.agents.base import BaseAgent, BaseMemory
from beeai_framework.agents.react import ReActAgent
from beeai_framework.agents.react.types import ReActAgentRunOutput
from beeai_framework.agents.types import (
    AgentExecutionConfig,
    AgentMeta,
)
from beeai_framework.backend.chat import ChatModel
from beeai_framework.backend.message import AssistantMessage, Message
from beeai_framework.context import Run
from beeai_framework.memory import ReadOnlyMemory, UnconstrainedMemory
from beeai_framework.template import PromptTemplateInput
from beeai_framework.tools.tool import Tool
from beeai_framework.utils.asynchronous import ensure_async
from beeai_framework.workflows.workflow import Workflow, WorkflowRun

AgentFactory = Callable[[ReadOnlyMemory], BaseAgent | Awaitable[BaseAgent]]


class AgentFactoryInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    llm: ChatModel
    instructions: str | None = None
    tools: list[InstanceOf[Tool]] | None = None
    execution: AgentExecutionConfig | None = None


class Schema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    messages: list[Message] = Field(min_length=1)
    final_answer: str | None = None
    new_messages: list[Message] = []


class AgentWorkflow:
    def __init__(self, name: str = "AgentWorkflow") -> None:
        self.workflow = Workflow(name=name, schema=Schema)

    def run(self, messages: list[Message]) -> Run[WorkflowRun]:
        return self.workflow.run(Schema(messages=messages))

    def del_agent(self, name: str) -> "AgentWorkflow":
        self.workflow.delete_step(name)
        return self

    def add_agent(
        self,
        agent: (
            BaseAgent | Callable[[ReadOnlyMemory], BaseAgent | asyncio.Future[BaseAgent]] | AgentFactoryInput | None
        ) = None,
        /,
        **kwargs: Any,
    ) -> "AgentWorkflow":
        if not agent:
            if not kwargs:
                raise ValueError("An agent object or keyword arguments must be provided")
            elif "agent" in kwargs:
                agent = kwargs.get("agent")
            else:
                agent = AgentFactoryInput.model_validate(kwargs, strict=False, from_attributes=True)
        elif kwargs:
            raise ValueError("Agent object required or keyword arguments required but not both")

        if isinstance(agent, BaseAgent):

            async def factory(memory: ReadOnlyMemory) -> BaseAgent:
                instance: BaseAgent = await ensure_async(agent)(memory.as_read_only()) if isfunction(agent) else agent
                instance.memory = memory
                return instance

            return self._add(agent.meta.name, factory)

        random_string = "".join(random.choice(string.ascii_letters) for _ in range(4))
        name = agent.name if not callable(agent) else f"Agent{random_string}"
        return self._add(name, agent if callable(agent) else self._create_factory(agent))

    def _create_factory(self, agent_input: AgentFactoryInput) -> AgentFactory:
        def factory(memory: BaseMemory) -> ReActAgent:
            def customizer(config: PromptTemplateInput) -> PromptTemplateInput:
                new_config = config.model_copy()
                new_config.defaults["instructions"] = agent_input.instructions or config.defaults.get("instructions")
                return new_config

            return ReActAgent(
                llm=agent_input.llm,
                tools=agent_input.tools or [],
                memory=memory,
                templates={"system": lambda template: template.fork(customizer=customizer)},
                meta=AgentMeta(name=agent_input.name, description=agent_input.instructions or "", tools=[]),
                execution=agent_input.execution,
            )

        return factory

    def _add(self, name: str, factory: AgentFactory) -> Self:
        async def step(state: Schema) -> None:
            memory = UnconstrainedMemory()
            for message in state.messages + state.new_messages:
                await memory.add(message)

            agent = await ensure_async(factory)(memory.as_read_only())
            run_output: ReActAgentRunOutput = await agent.run()
            state.final_answer = run_output.result.text
            state.new_messages.append(
                AssistantMessage(f"Assistant Name: {name}\nAssistant Response: {run_output.result.text}")
            )

        self.workflow.add_step(name, step)
        return self

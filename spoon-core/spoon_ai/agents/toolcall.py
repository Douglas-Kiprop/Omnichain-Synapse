# spoon_ai/agents/tool_call.py

import json
import asyncio
import time
from logging import getLogger
from typing import Any, List, Optional
import logging

from pydantic import Field
from termcolor import colored

from spoon_ai.agents.react import ReActAgent
from spoon_ai.prompts.toolcall import \
    NEXT_STEP_PROMPT as TOOLCALL_NEXT_STEP_PROMPT
from spoon_ai.prompts.toolcall import SYSTEM_PROMPT as TOOLCALL_SYSTEM_PROMPT
from spoon_ai.schema import TOOL_CHOICE_TYPE, AgentState, ToolCall, ToolChoice, Message, Role
from spoon_ai.tools import ToolManager
from mcp.types import Tool as MCPTool
from spoon_ai.tools.mcp_tool import MCPTool as SpoonMCPTool

logging.getLogger("spoon_ai").setLevel(logging.INFO)
logger = getLogger("spoon_ai")

class ToolCallAgent(ReActAgent):

    name: str = "toolcall"
    description: str = "Useful when you need to call a tool"

    system_prompt: str = TOOLCALL_SYSTEM_PROMPT
    next_step_prompt: str = TOOLCALL_NEXT_STEP_PROMPT

    avaliable_tools: ToolManager = Field(default_factory=ToolManager)
    special_tool_names: List[str] = Field(default_factory=list)
    tool_choices: TOOL_CHOICE_TYPE = ToolChoice.AUTO # type: ignore
    tool_calls: List[ToolCall] = Field(default_factory=list)
    output_queue: asyncio.Queue = Field(default_factory=asyncio.Queue)
    max_tool_output_length: Optional[int] = Field(default=4000, exclude=True)

    # MCP Tools Caching
    mcp_tools_cache: Optional[List[MCPTool]] = Field(default=None, exclude=True)
    mcp_tools_cache_timestamp: Optional[float] = Field(default=None, exclude=True)
    mcp_tools_cache_ttl: float = Field(default=300.0, exclude=True)

    async def _get_cached_mcp_tools(self) -> List[MCPTool]:
        current_time = time.time()
        if (self.mcp_tools_cache is not None and
            self.mcp_tools_cache_timestamp is not None and
            current_time - self.mcp_tools_cache_timestamp < self.mcp_tools_cache_ttl):
            return self.mcp_tools_cache

        if hasattr(self, "list_mcp_tools"):
            mcp_tools = await self.list_mcp_tools()
            self.mcp_tools_cache = mcp_tools
            self.mcp_tools_cache_timestamp = current_time
            return mcp_tools
        return []

    async def think(self) -> bool:
        if self.next_step_prompt:
            self.add_message("user", self.next_step_prompt)

        mcp_tools = await self._get_cached_mcp_tools()

        def convert_mcp_tool(tool: MCPTool) -> SpoonMCPTool:
            return SpoonMCPTool(
                name=tool.name,
                description=tool.description,
                parameters=tool.inputSchema,
            ).to_param()

        all_tools = self.avaliable_tools.to_params()
        mcp_tools_params = [convert_mcp_tool(tool) for tool in mcp_tools]
        
        unique_tools = {}
        for tool in all_tools + mcp_tools_params:
            unique_tools[tool["function"]["name"]] = tool
        unique_tools_list = list(unique_tools.values())

        response = await self.llm.ask_tool(
            messages=self.memory.messages,
            system_msg=self.system_prompt,
            tools=unique_tools_list,
            tool_choice=self.tool_choices,
            output_queue=self.output_queue,
        )

        if self._should_terminate_on_finish_reason(response):
            self.state = AgentState.FINISHED
            self.add_message("assistant", response.content or "Task completed")
            self._finish_reason_terminated = True
            self._final_response_content = response.content or "Task completed"
            return False

        self.tool_calls = response.tool_calls
        logger.info(colored(f"🤔 {self.name}'s thoughts: {response.content}", "cyan"))
        
        if self.output_queue:
            self.output_queue.put_nowait({"content": response.content})
            self.output_queue.put_nowait({"tool_calls": response.tool_calls})

        try:
            if self.tool_choices == ToolChoice.NONE:
                if response.tool_calls:
                    return False
                if response.content:
                    self.add_message("assistant", response.content)
                    return True
                return False
            
            self.add_message("assistant", response.content, tool_calls=self.tool_calls)
            
            if self.tool_choices == ToolChoice.REQUIRED and not self.tool_calls:
                return True
            if self.tool_choices == ToolChoice.AUTO and not self.tool_calls:
                return bool(response.content)
            return bool(self.tool_calls)
        except Exception as e:
            logger.error(f"{self.name} failed to think: {e}")
            self.add_message("assistant", f"Error encountered while thinking: {e}")
            return False

    async def run(self, request: Optional[str] = None) -> str:
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Agent {self.name} is not in the IDLE state")

        self.state = AgentState.RUNNING
        if request is not None:
            self.memory.add_message(Message(role=Role.USER, content=request))

        self._finish_reason_terminated = False
        self._final_response_content = None

        results: List[str] = []
        try:
            async with self.state_context(AgentState.RUNNING):
                while self.current_step < self.max_steps and self.state == AgentState.RUNNING:
                    self.current_step += 1
                    
                    # NOTE: We allow exceptions to bubble up from step() here
                    step_result = await self.step()
                    
                    if self.is_stuck():
                        self.handle_struck_state()

                    if hasattr(self, '_finish_reason_terminated') and self._finish_reason_terminated:
                        final_content = getattr(self, '_final_response_content', step_result)
                        self._finish_reason_terminated = False
                        if hasattr(self, '_final_response_content'):
                            delattr(self, '_final_response_content')
                        return final_content

                    results.append(f"Step {self.current_step}: {step_result}")

                if self.current_step >= self.max_steps:
                    results.append("Stuck in loop. Resetting state.")

            return "\n".join(results) if results else "No results"
        
        except Exception as e:
            # CRITICAL: If this is a Payment Exception, do NOT catch/log it as a generic error.
            # Reraise it immediately so the Server can catch it.
            if type(e).__name__ == "PaymentRequiredException":
                logger.info("💰 ToolCallAgent bubbling PaymentRequiredException up to Server...")
                raise e
            
            logger.error(f"Error during agent run: {e}")
            raise 
        finally:
            # 💡 CLEANUP FIX: Call clear() to reset messages, tool_calls, and state
            self.clear()
            
    async def step(self) -> str:
        should_act = await self.think()
        if not should_act:
            if self.state == AgentState.FINISHED:
                return "Task completed based on finish_reason signal"
            else:
                self.state = AgentState.FINISHED
                return "Thinking completed. No action needed."
        return await self.act()

    async def act(self) -> str:
        if not self.tool_calls:
            if self.tool_choices == ToolChoice.REQUIRED:
                raise ValueError("No tools to call")
            return self.memory.messages[-1].content or "No response from assistant"

        results = []
        for tool_call in self.tool_calls:
            result = await self.execute_tool(tool_call)
            self.add_message("tool", result, tool_call_id=tool_call.id)
            results.append(result)
        return "\n\n".join(results)

    async def execute_tool(self, tool_call: ToolCall) -> str:
        def parse_tool_arguments(arguments):
            if isinstance(arguments, str):
                arguments = arguments.strip()
                if not arguments: return {}
                try: return json.loads(arguments)
                except json.JSONDecodeError: return {}
            elif isinstance(arguments, dict): return arguments
            else: return {}

        if tool_call.function.name not in self.avaliable_tools.tool_map:
            if not hasattr(self, "call_mcp_tool"):
                raise ValueError(f"Tool {tool_call.function.name} not found")
            kwargs = parse_tool_arguments(tool_call.function.arguments)
            return await self.call_mcp_tool(tool_call.function.name, **kwargs)

        name = tool_call.function.name
        
        try:
            args = parse_tool_arguments(tool_call.function.arguments)
            result = await self.avaliable_tools.execute(name=name, tool_input=args)

            summarized_result = self._summarize_tool_output(result)
            observation = (
                f"Observed output of cmd {name} execution: {summarized_result}"
                if summarized_result else f"cmd {name} execution without any output"
            )

            self._handle_special_tool(name, summarized_result)
            return observation

        except Exception as e:
            # Reraise PaymentRequiredException immediately
            if type(e).__name__ == "PaymentRequiredException":
                logger.info(f"🛑 Payment required for {name} - Breaking execution loop!")
                raise e
            
            # For all other errors, return as string so the LLM can see it
            logger.error(f"❌ Tool execution error for {name}: {e}")
            return f"Error executing tool {name}: {str(e)}"

    def _summarize_tool_output(self, output: Any) -> str:
        if self.max_tool_output_length is None or output is None:
            return str(output)
        output_str = str(output)
        if len(output_str) > self.max_tool_output_length:
            return output_str[:self.max_tool_output_length] + "... (truncated)"
        return output_str

    def _handle_special_tool(self, name: str, result:Any, **kwargs):
        if not self._is_special_tool(name): return
        if self._should_finish_execution(name, result, **kwargs):
            self.state = AgentState.FINISHED

    def _is_special_tool(self, name: str) -> bool:
        return name.lower() in [n.lower() for n in self.special_tool_names]

    def _should_finish_execution(self, name: str, result: Any, **kwargs) -> bool:
        return True

    def _should_terminate_on_finish_reason(self, response) -> bool:
        finish_reason = getattr(response, 'finish_reason', None)
        native_finish_reason = getattr(response, 'native_finish_reason', None)
        if finish_reason == "stop":
            return native_finish_reason in ["stop", "end_turn"]
        return False

    def clear(self):
        # Clears conversation history and internal state
        self.memory.clear()
        self.tool_calls = []
        self.state = AgentState.IDLE
        self.current_step = 0
        self.mcp_tools_cache = None
        self.mcp_tools_cache_timestamp = None
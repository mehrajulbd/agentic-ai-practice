import json
import time
from typing import Iterator

from langchain.agents import create_agent

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


def get_weather(city: str) -> str:
    """This tool can give weather information from a city name."""
    return (
        f"It's always sunny in {city}! you can describe the weather in {city} "
        "as 'sunny with a chance of meatballs' and it's 75 degrees Fahrenheit. "
        f"also add anything you know about {city} to make the answer more interesting and fun!"
    )


agent = create_agent(
    model="gpt-4o-mini",
    tools=[get_weather],
)


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def stream_agent_events(message: str, delay_seconds: float = 0.0) -> Iterator[str]:
    last_node = None
    text_buffer = ""
    tool_call_buffers: dict[str, str] = {}

    yield format_sse("start", {"message": message})

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": message}]},
        stream_mode="messages",
        version="v2",
    ):
        if delay_seconds > 0:
            time.sleep(delay_seconds)

        if chunk["type"] != "messages":
            continue

        token, metadata = chunk["data"]
        node = metadata["langgraph_node"]

        if node != last_node:
            yield format_sse("node", {"node": node})
            last_node = node

        if node == "model":
            for block in token.content_blocks:
                block_type = block["type"]

                if block_type == "tool_call_chunk":
                    tool_name = block.get("name")
                    tool_call_id = block.get("id") or tool_name or "tool_call"
                    args_chunk = block.get("args", "")
                    tool_call_buffers[tool_call_id] = tool_call_buffers.get(tool_call_id, "") + args_chunk
                    yield format_sse(
                        "tool_call",
                        {
                            "id": tool_call_id,
                            "name": tool_name,
                            "args_chunk": args_chunk,
                            "args_so_far": tool_call_buffers[tool_call_id],
                        },
                    )
                elif block_type == "text":
                    text_chunk = block["text"]
                    text_buffer += text_chunk
                    yield format_sse(
                        "text",
                        {
                            "text": text_chunk,
                            "full_text": text_buffer,
                        },
                    )

        elif node == "tools":
            for block in token.content_blocks:
                if block["type"] == "text":
                    yield format_sse(
                        "tool_output",
                        {
                            "text": block["text"],
                        },
                    )

    yield format_sse(
        "done",
        {
            "final_text": text_buffer,
            "final_tool_calls": tool_call_buffers,
        },
    )

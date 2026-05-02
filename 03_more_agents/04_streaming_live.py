from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

def get_weather(city: str) -> str:
    """This tool can give weather information from a city name"""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="gpt-3.5-turbo",
    tools=[get_weather],
)

last_node = None
tool_call_buffer = ""
text_buffer = ""

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    stream_mode="messages",
    version="v2",
):
    if chunk["type"] != "messages":
        continue

    token, metadata = chunk["data"]
    node = metadata["langgraph_node"]

    # Detect node switch
    if node != last_node:
        if text_buffer:
            print(text_buffer.strip())
            text_buffer = ""
        if tool_call_buffer:
            print(tool_call_buffer.strip())
            tool_call_buffer = ""
        print(f"\n[{node.upper()}]")
        last_node = node

    # MODEL NODE
    if node == "model":
        for block in token.content_blocks:
            if block["type"] == "tool_call_chunk":
                # accumulate tool args
                tool_call_buffer += block.get("args", "")
            elif block["type"] == "text":
                text_buffer += block["text"]

    # TOOLS NODE
    elif node == "tools":
        for block in token.content_blocks:
            if block["type"] == "text":
                print(f"Tool Output → {block['text']}")

# Flush remaining text
if text_buffer:
    print(text_buffer.strip())

# Optional: show final parsed tool call
if tool_call_buffer:
    print("\n[TOOL CALL ARGS]")
    print(tool_call_buffer)
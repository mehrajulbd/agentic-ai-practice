from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.tools import tool
from typing import Callable
from dotenv import load_dotenv
load_dotenv()

# ------------------ TOOLS ------------------

@tool
def public_search(query: str) -> str:
    """Simulates a public search tool that anyone can use."""
    print(f"🔍 [PUBLIC SEARCH] Query: {query}")
    return f"Results for '{query}': [PUBLIC RESULT 1], [PUBLIC RESULT 2]"

@tool
def private_search(query: str) -> str:
    """Simulates a private search tool that only authenticated users can use."""
    print(f"🔐 [PRIVATE SEARCH] Query: {query}")
    return f"Results for '{query}': [PRIVATE RESULT 1], [PRIVATE RESULT 2]"

@tool
def advanced_search(query: str) -> str:
    """Simulates an advanced search tool that provides deeper insights."""
    print(f"🔬 [ADVANCED SEARCH] Query: {query}")
    return f"Results for '{query}': [ADVANCED RESULT 1], [ADVANCED RESULT 2]"


# ------------------ MIDDLEWARE ------------------

@wrap_model_call
def skill_unlock_system(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:

    state = request.state
    is_authenticated = state.get("authenticated", False)
    message_count = len(state["messages"])

    if not is_authenticated:
        allowed = ["public_search"]
        level = "🟢 Guest"
    elif message_count < 3:
        allowed = ["public_search", "private_search"]
        level = "🔵 Trusted"
    else:
        allowed = ["public_search", "private_search", "advanced_search"]
        level = "🟣 Power User"

    filtered_tools = [t for t in request.tools if t.name in allowed]

    # Attach metadata for visibility
    request.state["agent_level"] = level
    request.state["available_tools"] = allowed

    request = request.override(tools=filtered_tools)
    
    print("\n==============================")
    print(f"User: {request.state.get('messages')[-1].content}")
    print(f"Authenticated: {is_authenticated}")
    print(f"Agent Level: {level}")
    print(f"Available Tools: {allowed}")
    print("==============================\n")
    
    return handler(request)


# ------------------ AGENT ------------------

agent = create_agent(
    model="gpt-4o-mini",
    tools=[public_search, private_search, advanced_search],
    middleware=[skill_unlock_system]
)


# ------------------ DEMO LOOP ------------------

state = {
    "messages": [],
    "authenticated": False
}

def run_turn(user_input: str):
    state["messages"].append({"role": "user", "content": user_input})
    
    print(f"User Input: {user_input}")
    print(f"Current State: {state}\n")

    result = agent.invoke({
        "messages": state["messages"]
    }, state=state)

    state["messages"].append({"role": "assistant", "content": result["messages"][-1].content})
    
    print(f"AI Response: {result['messages'][-1].content}")


# ------------------ RUN DEMO ------------------

# Guest
run_turn("Use tools and Search latest AI news")

# 🔐 Authenticate user mid-session
print("🔐 User authenticated!\n")
state["authenticated"] = True

# Trusted
run_turn("Use tools and Search internal company docs")

# Power User
run_turn("Use tools and Compare multiple datasets with advanced search")
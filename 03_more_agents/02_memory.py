from langchain.agents import create_agent, AgentState
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv

load_dotenv()

class CustomAgentState(AgentState):
    user_id: str
    preferences: dict

@tool
def get_user_info(user_id: str):
    """Returns user info from a user id"""
    return f"user info for {user_id}: name: alex"

agent = create_agent(
    "gpt-4o-mini",
    tools=[get_user_info],
    state_schema=CustomAgentState,
    checkpointer=InMemorySaver(),
)

thread_id = "user_123_thread"

def chat_turn(user_message: str, user_id: str, preferences: dict):
    # Merge custom state into the run every turn
    input_state = {
            "messages": [
                {
                    "role": "system",
                    "content": f"Current user_id: {user_id}. Preferences: {preferences}"
                },
                {"role": "user", "content": user_message},
            ],
        "user_id": user_id,
        "preferences": preferences, 
    }

    result = agent.invoke(
        input_state,
        {"configurable": {"thread_id": thread_id}},
    )

    return result

# Turn 1
result1 = chat_turn(
    "Hello, what is my name?",
    user_id="user_123",
    preferences={"theme": "dark"},
)

print(result1["messages"][-1].content)

# Turn 2
result2 = chat_turn(
    "What theme do I prefer?",
    user_id="user_123",
    preferences={"theme": "dark"},
)

print(result2["messages"][-1].content)
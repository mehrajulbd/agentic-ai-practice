from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.tools import tool
from typing import Callable
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
load_dotenv()

state = {
    "messages": [],
    "token": None,
}

users = {
    "alex":{
        "username": "alex",
        "password": "1234"
    },
    "bob": {
        "username": "bob",
        "password": "4321"
    }
}

personal_data = {
    "alex": "Personal data: he is a humble guy.",
    "bob": "Personal data: he is a bad guy."
}

@tool
def get_personal_data() -> str:
    """Fetch personal data for a given name. Only available to authenticated users."""
    print(f"[TOOL] 🔐 Accessing personal data...")
    if state["token"] in personal_data:
        return personal_data[state["token"]]
    return "You do not have any personal data. Add some personal data first."

@tool
def add_personal_data(data: str) -> str:
    """Only available to authenticated users."""
    print(f"[TOOL] 🔐 Adding personal data for {state['token']}...")
    if state["token"] in personal_data:
        personal_data[state["token"]] = personal_data[state["token"]] + data
        return f"Personal data for {state['token']} added successfully."
    return "You do not have permission to add personal data. Please authenticate first."

@tool
def login_user(username: str, password: str) -> str:
    """Pass username and password to authenticate the user."""
    print(f"[TOOL] 🔐 Authenticating user username: {username} password: {password} ...")
    # Simulate authentication logic
    if username.lower() in users and users[username.lower()]["password"] == password:
        state["token"] = username.lower()
        return f"User {username} authenticated successfully."
    return "Invalid username or password. Please try again or register if you don't have an account."

@tool
def logout_user() -> str:
    """Logout the current user."""
    print(f"[TOOL] 🔐 Logging out user {state['token']}...")
    state["token"] = None
    return "User logged out successfully."

@tool
def register_user(username: str, password: str) -> str:
    """Register a new user with username and password."""
    print(f"[TOOL] 🔐 Registering user username: {username} password: {password} ...")
    if username.lower() in users:
        return "Username already exists. Please choose a different username."
    users[username.lower()] = {
        "username": username.lower(),
        "password": password
    }
    personal_data[username.lower()] = ""
    return f"User {username} registered successfully. You can now login to access personal data."

def run_turn(user_input: str):
    state["messages"].append({"role": "user", "content": user_input})
    
    print(f"User Input: {user_input}")
    print(f"Current State: {state}\n")
    
    tools = []
    if state["token"]:
        tools.append(get_personal_data)
        tools.append(add_personal_data)
        tools.append(logout_user)
    else:
        tools.append(login_user)
        tools.append(register_user)
             
    agent = create_agent(
        model="gpt-4o-mini",
        tools=tools,
    )

    result = agent.invoke({
        "messages": state["messages"]
    })

    state["messages"].append({"role": "assistant", "content": result["messages"][-1].content})
    
    print(f"AI Response: {result['messages'][-1].content}")


if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat...")
            break
        run_turn(user_input)
        
        # print("\n---\n")
        # print(f"Current Conversation State: {state}")
        # print("\n---\n")
from fileinput import filename

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.tools import tool
from typing import Callable
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import json
load_dotenv()

FILE_NAME = "conversation_summary.txt"

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

personal_data = {}


def write_json(filename, data):
    """Saves a Python dictionary or list to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            # indent=4 makes the JSON pretty and readable
            json.dump(data, file, indent=4)
        print(f"Data successfully saved to {filename}")
    except IOError as e:
        print(f"An error occurred while writing JSON: {e}")
        

def read_json(filename):
    """Reads a JSON file and returns the parsed Python object."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return "Error: JSON file not found."
    except json.JSONDecodeError:
        return "Error: Failed to decode JSON. Check if the file format is valid."
    except IOError as e:
        return f"An error occurred: {e}"

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
        write_json("personal_data.json", personal_data)
        return f"Personal data for {state['token']} added successfully."
    return "You do not have permission to add personal data. Please authenticate first."

@tool
def login_user(username: str, password: str) -> str:
    """Pass username and password to authenticate the user."""
    print(f"[TOOL] 🔐 Authenticating user username: {username} password: {password} ...")
    # Simulate authentication logic
    if username.lower() in users and users[username.lower()]["password"] == password:
        state["token"] = username.lower()
        if state["token"] not in personal_data:
            personal_data[state["token"]] = ""
            write_json("personal_data.json", personal_data)
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

def load_conversation():
    print(f"[UTILITY] 📂 Loading conversation...")
    # Simulate loading conversation from a file
    try:
        with open(FILE_NAME, 'r', encoding='utf-8') as file:
            content = file.read()
            state["messages"] = [{"role": "user", "content": f"Previous conversation summary: {content}"}]
            return True
    except FileNotFoundError:
        print("Error: The file was not found.")
        return False
    except IOError as e:
        print(f"An error occurred while reading: {e}")
        return False

def save_conversation(summary: str):
    print(f"[UTILITY] 💾 Saving conversation...")
    # Save the conversation summary in a file
    try:
        with open(FILE_NAME, 'w', encoding='utf-8') as file:
            file.write(summary)
        print(f"Successfully written to {FILE_NAME}")
    except IOError as e:
        print(f"An error occurred while writing: {e}")
        return False
    return True

def summarize_context():
    print(f"[UTILITY] 🧠 Summarizing conversation context...")
    agent = create_agent(
        model="gpt-4o-mini",
        system_prompt="Summarize the following conversation in a concise manner. Make sure to write all the historic details about the conversation, including user inputs and assistant responses. The summary should be comprehensive enough to provide context for future interactions without needing to refer back to the original messages. but not unnecessarily large.",
    )
    
    result = agent.invoke({
        "messages": state["messages"]
    })
    summary = result["messages"][-1].content
    
    save_conversation(summary)
    return summary

def run_turn(user_input: str):
    
    if len(state["messages"]) > 4:
        summary = summarize_context()
        state["messages"] = [{"role": "user", "content": f"Conversation summary so far: {summary}"}]
    
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
        model="openrouter:google/gemma-4-31b-it:free",
        tools=tools,
    )

    result = agent.invoke({
        "messages": state["messages"]
    })

    state["messages"].append({"role": "assistant", "content": result["messages"][-1].content})
    
    print(f"AI Response: {result['messages'][-1].content}")


if __name__ == "__main__":
    if load_conversation():
        print("Conversation loaded successfully.")
    personal_data_from_file = read_json("personal_data.json")
    print(f"Personal data from file: {personal_data_from_file}")
    if isinstance(personal_data_from_file, dict):
        personal_data.update(personal_data_from_file)
        print("Personal data loaded successfully.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat...")
            break
        run_turn(user_input)
        
        # print("\n---\n")
        # print(f"Current Conversation State: {state}")
        # print("\n---\n")
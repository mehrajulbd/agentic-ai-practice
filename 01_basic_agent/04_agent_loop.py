import math
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

# 1. Local Inventory State
inventory = {"apple": 5, "potion": 2, "scroll": 3}

@tool
def inventory_manager(action: str, item: str) -> str:
    """
    This tool manages the user's inventory. 
    Actions: 'consume' (deducts 1) or 'check' (returns count).
    args:
    - action: "consume" or "check"
    - item: name of the inventory item (e.g., "apple", "potion", "scroll")
    returns: A string message indicating the result of the action.
    """
    item = item.lower()
    if action == "check":
        count = inventory.get(item, 0)
        print(f"[TOOL] Checked {item}. Count: {count}")
        return f"You have {count} {item}(s)."
    
    if action == "consume":
        if inventory.get(item, 0) > 0:
            inventory[item] -= 1
            print(f"[TOOL] Consumed 1 {item}. Remaining: {inventory[item]}")
            return f"Success: Used 1 {item}. Remaining: {inventory[item]}"
        else:
            print(f"[TOOL] Failure: You don't have any {item}s left.")
            return f"Failure: You don't have any {item}s left."
    
    print(f"[TOOL] Invalid action: {action}")
    return "Invalid action."

# 2. Setup Agent
model = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
tools = [inventory_manager]

agent = create_agent(model, tools, system_prompt="You are an adventurer AI managing your inventory. Respond to user commands to check or consume items. Always update the inventory accordingly.")

# 3. The Natural Language Loop
print("--- Adventurer AI Ready ---")
print(f"Starting Inventory: {inventory}")

while True:
    user_input = input("\nWhat would you like to do? (or 'quit'): ")
    if user_input.lower() in ["quit", "exit"]:
        break

    # The agent decides which tool to call based on the natural language input
    response = agent.invoke({"messages": [("user", user_input)]})

    print(f"AI: {response['messages'][-1].content}")
    print(f"(Internal Inventory State: {inventory})")
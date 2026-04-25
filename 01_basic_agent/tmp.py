import math
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

# 1. Local Inventory State
game_state = {
    "inventory": {"elixir": 200000, "gold": 300000, "archer": 100, "barbarian": 200},
    "cost": {"archer": 100, "barbarian": 150, "level_1_wall": 50000, "level_2_wall": 100000},
    "base": {"level_1_wall": 100, "level_2_wall": 50},
    "enemy_inventory": {"archer": 150, "barbarian": 250}
}

@tool
def train_army(troop_name: str, quantity: str) -> str:
    """
    Train a specified quantity of troops.
    args:
    - troop_name: The type of troop to train (e.g., "archer", "barbarian").
    - quantity: The number of troops to train.
    returns: A message indicating success or failure of the training action.
    """
    if troop_name not in game_state["cost"]:
        return f"Error: {troop_name} is not a valid troop type."

    try:
        quantity = int(quantity)
    except ValueError:
        return "Error: Quantity must be a number."

    total_cost = game_state["cost"][troop_name] * quantity

    if game_state["inventory"]["elixir"] < total_cost:
        return f"Not enough elixir to train {quantity} {troop_name}(s). You need {total_cost} elixir but have {game_state['inventory']['elixir']} elixir."

    game_state["inventory"]["elixir"] -= total_cost
    game_state["inventory"][troop_name] += quantity
    
    print(f"[TOOL] Trained {quantity} {troop_name}(s). Remaining elixir: {game_state['inventory']['elixir']}.")

    return f"Trained {quantity} {troop_name}(s). Remaining elixir: {game_state['inventory']['elixir']}."

@tool
def check_game_state() -> str:
    """
    Check the current status of your inventory.
    returns: A formatted string showing the current inventory status.
    """
        
    print(f"[TOOL] Checked inventory:\n{game_state}")
    return game_state

@tool
def attack_enemy() -> str:
    """
    Use this tool to attack the enemy.
    returns: A formatted string showing the result of the attack.
    """
    result = ""
    my_troops = game_state["inventory"].get("archer", 0) + game_state["inventory"].get("barbarian", 0)
    enemy_troops = game_state["enemy_inventory"].get("archer", 0) + game_state["enemy_inventory"].get("barbarian", 0)

    if my_troops == 0:
        return "You have no troops to attack with!"

    if enemy_troops == 0:
        return "The enemy has no troops to defend with! You win by default."
    
    if my_troops > enemy_troops:
        result += "You won the battle!"
    elif my_troops < enemy_troops:
        result += "You lost the battle!"
    else:
        result += "The battle was a draw!"

    print(f"[TOOL] Attacked enemy. My troops: {my_troops}, Enemy troops: {enemy_troops}. Result: {result}")
    
    return result

@tool
def check_base() -> str:
    """
    Check the current status of your base defenses.
    returns: A formatted string showing the base defense status.
    """
    base_status = "Base Defense Status:\n"
    for item, level in game_state["base"].items():
        base_status += f"- {item}: Quantity {level}\n"
        
    print(f"[TOOL] Checked base defenses:\n{base_status}")
    return base_status

@tool
def enhance_base(item: str, quantity: int) -> str:
    """
    Upgrade a specific item in your base defenses.
    args:
    - item: The item to upgrade (e.g., "level_1_wall", "level_2_wall").
    - quantity: The number of times to upgrade the item.
    returns: A message indicating success or failure of the upgrade action.
    """
    if item not in game_state["base"]:
        return f"Error: {item} is not a valid base item."

    if game_state["inventory"]["gold"] < game_state["cost"][item] * quantity:
        return f"Not enough gold to upgrade {item}. You need {game_state['cost'][item] * quantity} gold but have {game_state['inventory']['gold']} gold."

    game_state["inventory"]["gold"] -= game_state["cost"][item] * quantity
    game_state["base"][item] += quantity

    print(f"[TOOL] Upgraded {item} to level {game_state['base'][item]}. Remaining gold: {game_state['inventory']['gold']}.")
    return f"Upgraded {item} to quantity {game_state['base'][item]}. Remaining gold: {game_state['inventory']['gold']}."

# 2. Setup Agent
model = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
tools = [train_army, check_game_state, attack_enemy, check_base, enhance_base]

agent = create_agent(model, tools, system_prompt="You are an adventurer in a strategy game. Your goal is to manage your resources, train troops, enhance your base defenses, and attack enemies to win battles. Always use the provided tools to achieve your objectives. Always check your inventory and base status using tool calling before making decisions. Before attacking check the game state and then prepare my inventory and enemy inventory then call the tool to attack the enemy.")

# 3. The Natural Language Loop
print("--- Clash of Clans Ready ---")
print(f"Starting State: {game_state}")

while True:
    user_input = input("\nWhat would you like to do? (or 'quit'): ")
    if user_input.lower() in ["quit", "exit"]:
        break

    # The agent decides which tool to call based on the natural language input
    response = agent.invoke({"messages": [("user", user_input)]})

    print(f"AI: {response['messages'][-1].content}")
    print(f"(Current Game State: {game_state})")
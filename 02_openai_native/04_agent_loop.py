from openai import OpenAI
from pydantic import BaseModel
from typing import Literal, Optional
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()

# 1. Define the Structured Schema
class InventoryAction(BaseModel):
    action: Literal["consume", "check", "none"]
    item: str
    amount: int
    thought_process: str 

# 2. Local State
inventory = {"apple": 5, "potion": 2, "scroll": 10}

def run_inventory_loop():
    print("--- RPG Inventory (Structured Output Mode) ---")
    
    while True:
        user_prompt = input("\nWhat do you want to do? (type 'exit' to stop): ")
        if user_prompt.lower() == "exit":
            break

        # 3. Call OpenAI with Response Format
        completion = client.beta.chat.completions.parse(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": f"You are an inventory assistant. Current items: {inventory}. Parse the user intent."},
                {"role": "user", "content": user_prompt},
            ],
            response_format=InventoryAction,
        )

        # 4. Extract Parsed Data
        result = completion.choices[0].message.parsed
        item = result.item.lower()
        
        print(f"AI Thought: {result.thought_process}")

        # 5. Logic Execution
        if result.action == "consume":
            if item in inventory and inventory[item] >= result.amount:
                inventory[item] -= result.amount
                print(f"ACTION: Consumed {result.amount} {item}(s). Success!")
            else:
                print(f"ACTION: Failed. You don't have enough {item}(s).")
        
        elif result.action == "check":
            count = inventory.get(item, 0)
            print(f"ACTION: You have {count} {item}(s) in your bag.")
            
        else:
            print("AI didn't find a valid inventory action.")

        print(f"Current Inventory: {inventory}")

if __name__ == "__main__":
    run_inventory_loop()
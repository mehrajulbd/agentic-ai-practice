import json
import math
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

# 1. Define your Python function
def advanced_calculator(expression: str) -> float:
    # 1. Get all functions from math
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    
    # 2. ALSO add the 'math' module itself to the dictionary
    allowed_names["math"] = math 
    
    # Now eval can handle both "sqrt(256)" AND "math.sqrt(256)"
    ans = eval(expression, {"__builtins__": {}}, allowed_names)
    
    print(f"\n[CALCULATOR TOOL] Calculated: {expression} = {ans}")
    return ans

# 2. Define the tool schema so the LLM knows how to format the JSON request
tools = [
    {
        "type": "function",
        "function": {
            "name": "advanced_calculator",
            "description": "Evaluates math. Use python math syntax. Example: 'sqrt(256) + log10(1000)'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A valid python math expression.",
                    },
                },
                "required": ["expression"],
            },
        }
    }
]

# Create the initial conversation history
messages = [
    {"role": "user", "content": "What is the square root of 256 added to the log base 10 of 1000?"}
]

print("Sending initial request to the LLM...")

# 3. Prompt the model with the tools defined
response = client.chat.completions.create(
    model="gpt-5-mini", # Or your preferred model
    messages=messages,
    tools=tools,
    tool_choice="auto" # Let the model decide if it needs the tool
)

# Extract the model's message (which contains the tool call request)
response_message = response.choices[0].message

# Save the model's tool call request to the conversation history
messages.append(response_message)

# 4. Check if the model decided to call our tool
if response_message.tool_calls:
    for tool_call in response_message.tool_calls:
        if tool_call.function.name == "advanced_calculator":
            
            # Extract the JSON arguments the LLM generated
            args = json.loads(tool_call.function.arguments)
            expression_to_evaluate = args["expression"]
            
            # --- THIS IS THE MANUAL EXECUTION ---
            # Run the local python function
            calc_result = advanced_calculator(expression_to_evaluate)
            
            # 5. Hand the result back to the LLM 
            # Note the role is "tool" so the LLM knows this is system data
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": str(calc_result), # Must be a string
            })

    print("\nSending tool results back for final synthesis...")
    
    # 6. Make a second call so the LLM can generate a conversational response
    final_response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
    )

    print("\nFinal Output:")
    print("-" * 20)
    print(final_response.choices[0].message.content)
else:
    print("The model decided not to use the tool.")
    print(response_message.content)
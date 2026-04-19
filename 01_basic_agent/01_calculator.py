import math
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

@tool
def advanced_calculator(expression: str) -> float:
    """
    Evaluates advanced mathematical expressions using python's math library.
    Use this for complex calculations like sin(x), log(x), sqrt(x), etc.
    Input must be a valid python math expression.
    
    args:
        expression: A string containing a valid python math expression. 
                    Example: "sqrt(256) + log10(1000)"
    returns:
        The result of the evaluated expression as a float.
    """
    # 1. Get all functions from math
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    
    # 2. ALSO add the 'math' module itself to the dictionary
    allowed_names["math"] = math 
    
    # Now eval can handle both "sqrt(256)" AND "math.sqrt(256)"
    ans = eval(expression, {"__builtins__": {}}, allowed_names)
    
    print(f"\n[CALCULATOR TOOL] Calculated: {expression} = {ans}")
    return ans

model = ChatOpenAI(model="gpt-5-mini")
tools = [advanced_calculator]
agent = create_agent(model, tools)

response = agent.invoke({"messages": 
    [("user", "Use tool and calculate: 1+2.4+root(16)+log_10base(100)+9.999+0.0001")]})
print(response["messages"][-1].content)


print("\n\n\n\n\n")
print(response)
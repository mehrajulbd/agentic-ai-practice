from typing import Generic, Union

from langchain.agents import create_agent
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

class Address(BaseModel):
    house: str
    road: str
    city: str
    postal_code: int
    country: str


agent = create_agent(
    model="google_genai:gemini-2.5-flash-lite",
    response_format= Address,
    system_prompt="You are an address parser, parse user address and format it properly. If there is not enough data assume it as unknown",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "148/D, Hi rise garden, chittagong-2409"}]}
)
print(result["messages"][-1].content_blocks)
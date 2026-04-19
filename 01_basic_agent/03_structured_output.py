from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
from pydantic import BaseModel

    
load_dotenv()

class Address(BaseModel):
    house: str
    road: str
    city: str
    postal_code: int
    country: str

model = ChatOpenAI(model="gpt-5-mini")
agent = create_agent(model, system_prompt="You are an address parser, parse user address and format it properly. If there is not enough data assume it as unknown", response_format=Address)


response = agent.invoke({"messages": [("user", "148/D, Hi Rise Garden View, Khulshi Green Housing Society, Khulshi-4209, Chattogram, Bangladesh")]})
print(response["messages"][-1].content)
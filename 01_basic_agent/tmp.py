import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(model="gpt-3.5-turbo")

agent = create_agent(model)

response = agent.invoke({
    "messages": [
        ("user", "1+2.4+root(16)+log_10base(100)+9.999+0.0001"),
    ]
})
print(response["messages"][-1].content)


print("\n\n\n\n\n")
print(response)
# COT, Few Shot, React
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
from pydantic import BaseModel

    
load_dotenv()

model = ChatOpenAI(model="gpt-4o")
agent = create_agent(model, system_prompt="Follow the user shown method to answer questions.")

few_shot_prompt={
    "messages": [
        ("user", """
         I want direct answers to my questions without any explanation. Follow the format shown below:
         Q:what is sin(90)+cos(90)
         A: 1
         Q: what is sqrt of 36
         A: 6
         Q: what is (sin(60)*sin(60) - 1) / cos(pi/3)
         A:
         """),
    ]
}

chain_of_thought_prompt={
    "messages": [
        ("user", """
         I want you to break down the problem and show your work before giving the final answer. Follow the format shown below:
         Q: what is sin(90)+cos(90)
         A: Lets break it down first, value of sin(90) is 1 and cos(90) is 0. So, by adding both we can say that the ans is 1
         Q: what is sqrt of 36"
         A: Lets Break it down first. As 36 is a square number and 6*6 is 36 so sqrt of 36 will be 6
         Q: what is (sin(60)*sin(60) - 1) / cos(pi/3)
         A:
         """),

    ]
}

response = agent.invoke(few_shot_prompt)
print("Few Shot Prompt Response:")
print(response["messages"][-1].content)


response = agent.invoke(chain_of_thought_prompt)
print("Chain of Thought Prompt Response:")
print(response["messages"][-1].content)
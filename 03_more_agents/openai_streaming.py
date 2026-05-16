import time

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI()

stream = client.responses.create(
    model="gpt-5-mini",
    input=[
        {
            "role": "user",
            "content": "Say 'double bubble bath' ten times fast.",
        },
    ],
    stream=True,
)

for event in stream:
    time.sleep(0.1)  # simulate processing time
    print(event)
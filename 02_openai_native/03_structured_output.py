from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

class Address(BaseModel):
    house: str
    road: str
    city: str
    postal_code: int
    country: str

response = client.responses.parse(
    model="gpt-5-mini",
    input=[
        {"role": "system", "content": "You are an address parser, parse user address and format it properly. If there is not enough data assume it as unknown"},
        {
            "role": "user",
            "content": "148/D, Hi Rise Garden View, Khulshi Green Housing Society, Khulshi-4209, Chattogram, Bangladesh.",
        },
    ],
    text_format=Address,
)

address : Address = response.output_parsed
print("The user is from " + address.country)
print(address.model_dump_json(indent=4))
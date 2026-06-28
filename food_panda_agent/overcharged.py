from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from models import current_order


# automatically verify if he is overcharged and file complain with some info if he is overcharged
# if he is not overcharged then collect user story and file complain
# talk human

@tool
def talk_to_human():
    """This function allows the user to speak to a human representative for further assistance."""
    return "Please call our support hotline at 123-456-7890 for further assistance."

@tool
def inquire_order_information(user_query: str):
    """This function takes a user query as input and provides information about the order based on the query."""
    current_order_info_str = current_order.model_dump_json(indent=2)
    system_prompt = f"You are a helpful assistant for Food Panda customer support. You can provide information about the order and refund based on the user's query. the current order information is as follows: {current_order_info_str}"
    
    model = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
    agent = create_agent(model, system_prompt=system_prompt)
    response = agent.invoke({"messages": [("user", user_query)]})
    
    print(f"[TOOL] {response['messages'][-1].content}")
    return response['messages'][-1].content

@tool
def get_order_information():
    """This function provides information about the order or refund."""
    current_order_info_str = current_order.model_dump_json(indent=2)
    print(f"[TOOL] The current order information is as follows: {current_order_info_str}")
    return f"The current order information is as follows: {current_order_info_str}"

@tool
def verify_overcharge():
    """This function verifies if the user has been overcharged based on the current order information."""
    total_item_cost = sum(item.quantity * item.price for item in current_order.items)
    total_cost_with_fees = total_item_cost + current_order.other_fees
    
    if total_cost_with_fees < current_order.total_amount:
        extra_charged_amount =  current_order.total_amount - total_cost_with_fees
        verdict = f"You have been overcharged by ${extra_charged_amount}. The total cost with fees is ${total_cost_with_fees}, while the total amount charged is ${current_order.total_amount}."
        print(f"[TOOL] {verdict}")
        return verdict
    elif total_cost_with_fees > current_order.total_amount:
        undercharged_amount = total_cost_with_fees - current_order.total_amount
        verdict = f"You have been undercharged by ${undercharged_amount}. The total cost with fees is ${total_cost_with_fees}, while the total amount charged is ${current_order.total_amount}."
        print(f"[TOOL] {verdict}")
        return verdict
    else:
        verdict = f"You have not been overcharged. The total cost with fees is ${total_cost_with_fees}, which matches the total amount charged of ${current_order.total_amount}."
        print(f"[TOOL] {verdict}")
        return verdict

@tool
def file_verified_overcharged_complain(refund_method: str, refund_amount: float, refund_address: str, additional_details: str):
    """This function files a complaint for the user if they have been verified to be overcharged. It collects necessary data from the user and files the complaint."""
    complaint_details = {
        "refund_method": refund_method,
        "refund_amount": refund_amount,
        "refund_address": refund_address,
        "additional_details": additional_details,
        "order_id": current_order.order_id,
        "customer_name": current_order.customer.name,
        "customer_email": current_order.customer.email,
        "customer_phone": current_order.customer.phone,
        "restaurant_name": current_order.restaurant.name,
        "restaurant_address": current_order.restaurant.address,
        "restaurant_phone": current_order.restaurant.phone,
        "total_amount": current_order.total_amount,
        "other_fees": current_order.other_fees,
        "order_timestamp": current_order.order_timestamp,
        "delivery_address": current_order.delivery_address,
        "delivery_timestamp": current_order.delivery_timestamp,
    }
    print(f"[TOOL] Complaint filed with the following details: {complaint_details}")
    return f"Complaint filed with the following details: {complaint_details}"

@tool
def file_verified_undercharged_complain(payment_method: str, payment_amount: float, payment_address: str, additional_details: str):
    """This function files a complaint for the user if they have been verified to be overcharged. It collects necessary data from the user and files the complaint."""
    complaint_details = {
        "payment_method": payment_method,
        "payment_amount": payment_amount,
        "payment_address": payment_address,
        "additional_details": additional_details,
        "order_id": current_order.order_id,
        "customer_name": current_order.customer.name,
        "customer_email": current_order.customer.email,
        "customer_phone": current_order.customer.phone,
        "restaurant_name": current_order.restaurant.name,
        "restaurant_address": current_order.restaurant.address,
        "restaurant_phone": current_order.restaurant.phone,
        "total_amount": current_order.total_amount,
        "other_fees": current_order.other_fees,
        "order_timestamp": current_order.order_timestamp,
        "delivery_address": current_order.delivery_address,
        "delivery_timestamp": current_order.delivery_timestamp,
    }
    print(f"[TOOL] Complaint filed with the following details: {complaint_details}")
    return f"Complaint filed with the following details: {complaint_details}"


@tool
def file_unverified_overcharged_complain(user_story: str):
    """This function files a complaint for the user if they have not been verified to be overcharged. It collects the user's story and files the complaint."""
    complaint_details = {
        "user_story": user_story,
        "order_id": current_order.order_id,
        "customer_name": current_order.customer.name,
        "customer_email": current_order.customer.email,
        "customer_phone": current_order.customer.phone,
        "restaurant_name": current_order.restaurant.name,
        "restaurant_address": current_order.restaurant.address,
        "restaurant_phone": current_order.restaurant.phone,
        "total_amount": current_order.total_amount,
        "other_fees": current_order.other_fees,
        "order_timestamp": current_order.order_timestamp,
        "delivery_address": current_order.delivery_address,
        "delivery_timestamp": current_order.delivery_timestamp,
    }
    print(f"[TOOL] Complaint filed with the following details: {complaint_details}")
    return f"Complaint filed with the following details: {complaint_details}"

tools = [talk_to_human, inquire_order_information, get_order_information, file_verified_overcharged_complain, file_unverified_overcharged_complain, file_verified_undercharged_complain]

class ChatOutput(BaseModel):
    response: str
    is_finished: bool

def handle_overcharged():
    
    messages = [
        HumanMessage(content="The payment amount was incorrect in this order."),
    ]
    
    result = verify_overcharge.invoke({})
    messages.append(AIMessage(content=f"{result}."))
    
    
    while True:
        choice = input()
        model = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
        agent = create_agent(model, tools = tools, system_prompt="Based on the current order information you need to help the user to verify if he has been overcharged and file complain with necessary data collected from the user if he has been overcharged. If he has not been overcharged then you need to collect user story and file complain. You can also provide information about the order or refund based on the user's query. you can also help user to talk to a human representative.If you think that the conversation is completed about overcharged then return is_finished as True", response_format=ChatOutput)
        messages.append(HumanMessage(content=choice))
        
        # response = agent.invoke({"messages": [("user", choice)]})
        response = agent.invoke({"messages": messages})
        structured_response : ChatOutput = response["structured_response"]
        print(f"[AI RESPONSE]{structured_response.response}")
        
        if structured_response.is_finished:
            break

        messages.append(AIMessage(content=structured_response.response))
        
        
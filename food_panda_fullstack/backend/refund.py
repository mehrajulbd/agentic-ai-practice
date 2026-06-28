from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from models import current_order


# get information about order / refund - DONE
# refund method change - (guardrail: only if refund status is pending, otherwise ignore and exit) - DONE
# complain place (guardrail: to currant day diff) - DONE
# talk to human (send phone) - (guardrail: only if refund status is pending or rejected, otherwise ignore and exit) - DONE
# prompt: other cases (overcharge, invoice, voucher, points, general feedback) --- IGNORE and EXIT ---

@tool
def talk_to_human():
    """This function allows the user to speak to a human representative for further assistance."""
    if current_order.refund_status in ["Pending", "Rejected"]:
        print("[TOOL] Please call our support hotline at 123-456-7890 for further assistance.")
        return "Please call our support hotline at 123-456-7890 for further assistance."
    else:
        print(f"[TOOL] You can only speak to a human representative if your refund status is pending or rejected. Your current refund status is {current_order.refund_status}, which does not meet this criteria, so you cannot speak to a human representative at this time.")
        return f"You can only speak to a human representative if your refund status is pending or rejected. Your current refund status is {current_order.refund_status}, which does not meet this criteria, so you cannot speak to a human representative at this time."

@tool
def complain_place():
    """This function allows the user to file a complaint about their order or refund."""
    order_date = current_order.order_date
    from datetime import datetime
    current_date = datetime.now()
    diff_days = (current_date - order_date).days
    
    if diff_days <= 7:
        print(f"[TOOL] You can file a complaint about your order or refund. Please provide details about your complaint and we will look into it.")
        return "You can file a complaint about your order or refund. Please provide details about your complaint and we will look into it."
    else:
        print(f"[TOOL] We apologize for the inconvenience. However, complaints can only be filed within 7 days of the order date. Your order was placed {diff_days} days ago, so unfortunately, you cannot file a complaint at this time.")
        return f"We apologize for the inconvenience. However, complaints can only be filed within 7 days of the order date. Your order was placed {diff_days} days ago, so unfortunately, you cannot file a complaint at this time."

@tool
def refund_method_change(new_refund_method: str):
    """This function takes a new refund method as input and updates the refund method for the current order if the refund status is pending."""
    if current_order.refund_status == "Pending":
        current_order.refund_method = new_refund_method
        print(f"[TOOL] Your refund method has been updated to {new_refund_method}.")
        return f"Your refund method has been updated to {new_refund_method}."
    else:
        print("[TOOL] Refund method change is only allowed when the refund status is pending. Your current refund status is not pending, so the refund method cannot be changed.")
        return "Refund method change is only allowed when the refund status is pending. Your current refund status is not pending, so the refund method cannot be changed."

@tool
def inquire_order_or_refund_information(user_query: str):
    """This function takes a user query as input and provides information about the order or refund based on the query."""
    current_order_info_str = current_order.model_dump_json(indent=2)
    system_prompt = f"You are a helpful assistant for Food Panda customer support. You can provide information about the order and refund based on the user's query. the current order information is as follows: {current_order_info_str}"
    
    model = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
    agent = create_agent(model, system_prompt=system_prompt)
    response = agent.invoke({"messages": [("user", user_query)]})
    
    print(f"[TOOL] {response['messages'][-1].content}")
    return response['messages'][-1].content

@tool
def get_order_or_refund_information():
    """This function provides information about the order or refund."""
    current_order_info_str = current_order.model_dump_json(indent=2)
    print(f"[TOOL] The current order information is as follows: {current_order_info_str}")
    return f"The current order information is as follows: {current_order_info_str}"

tools = [inquire_order_or_refund_information, refund_method_change, complain_place, talk_to_human]

class RefundChatOutput(BaseModel):
    response: str
    is_finished: bool

def handle_refund(initial_messages: list[tuple[str, str]], user_message: str) -> tuple[str, bool]:
    
    messages = []
    for msg in initial_messages:
        if msg[0] == "human":
            messages.append(HumanMessage(content=msg[1]))
        elif msg[0] == "ai":
            messages.append(AIMessage(content=msg[1]))
    
    model = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
    agent = create_agent(model, tools = tools, system_prompt="Based on the current order information and refund status, the user may want to inquire about their order or refund, change their refund method (only if the refund status is pending), file a complaint (only if the order was placed within the last 7 days and validate this info using tool as the human may lie), or speak to a human representative (only if the refund status is pending or rejected). Please determine the user's intent based on their input and invoke the appropriate tool to assist them. If you think that the conversation is completed about refund then return is_finished as True", response_format=RefundChatOutput)
    messages.append(HumanMessage(content=user_message))
    response = agent.invoke({"messages": messages[-6:]})
    structured_response : RefundChatOutput = response["structured_response"]
    print(f"[AI RESPONSE]{structured_response.response}")
    
    return structured_response.response, structured_response.is_finished
        
        
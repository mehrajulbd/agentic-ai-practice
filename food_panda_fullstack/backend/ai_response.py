from pydantic import BaseModel

from refund import handle_refund

class SupportChatRequest(BaseModel):
    session_id: str
    message: str
    option_id: int

class SupportChatResponse(BaseModel):
    message: str
    is_completed: bool

def get_ai_response(user_request: SupportChatRequest, messages: list[tuple[str, str]]) -> SupportChatResponse:
    
    res = ""
    is_completed = False
    
    if user_request.option_id == 1:
        res = "The refund turnaround time is 10-12 business days."
        is_completed = True
    elif user_request.option_id == 2:
        res, is_completed = handle_refund(messages, user_request.message)
    elif user_request.option_id == 3:
        print("2")
    elif user_request.option_id == 4:
        print("2")
    elif user_request.option_id == 5:
        print("2")
    elif user_request.option_id == 6:
        print("2")
    else:
        print("invalid")
    
    return SupportChatResponse(
        message=res,
        is_completed=is_completed
    )
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from chroma_helper import seed_rag_kb, get_kb_documents, delete_kb_document
from streaming import stream_agent_events
from ai_response import get_ai_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Hello, FastAPI!"}


class DocumentIngestRequest(BaseModel):
    doc: str
    metadata: dict


class ChatStreamRequest(BaseModel):
    message: str
    delay_seconds: float = 0.12
    
class SupportChatRequest(BaseModel):
    session_id: str
    message: str
    option_id: int


sessions = {}

@app.post("/kb/ingest")
def ingest_doc(request: DocumentIngestRequest):
    
    doc_id = seed_rag_kb(
        knowledge=request.doc,
        metadata=request.metadata
    )
    
    return {
        "id": doc_id,
        "message": "Document ingested successfully",
        "doc": request.doc,
        "metadata": request.metadata
    }

@app.get("/kb")
def get_kb():
    docs = get_kb_documents()
    return {
        "documents": docs
    }
    
    
@app.delete("/kb/{doc_id}")
def delete_doc(doc_id: str):
    """
    Deletes a document from the RAG knowledge base by its ID.
    """
    res = delete_kb_document(doc_id=doc_id)
    return {
        "message": f"Document with ID {doc_id} deleted successfully.",
        "result": res
    }


@app.post("/chat/stream")
def chat_stream(request: ChatStreamRequest):
    return StreamingResponse(
        stream_agent_events(
            message=request.message,
            delay_seconds=request.delay_seconds,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/chat")
def chat(request: SupportChatRequest):
    """
    Handles a chat request and returns the agent's response.
    """
    if(request.session_id not in sessions):
        sessions[request.session_id] = []
        
    res = get_ai_response(request, sessions[request.session_id])
    
        
    sessions[request.session_id].append(("human", request.message))
    sessions[request.session_id].append(("ai", res.message))
    
    messages = sessions[request.session_id]
    
    if res.is_completed:
        sessions[request.session_id] = []
    
    return {
        "ai_response" : res.message,
        "is_completed": res.is_completed,
        "chat_history": messages
    }
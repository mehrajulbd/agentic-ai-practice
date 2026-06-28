from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_core.documents import Document
import chromadb
from uuid_utils import uuid4
from dotenv import load_dotenv

load_dotenv()

def get_chroma_client(collection_name: str):
    """
    Initializes and returns a Chroma client connected to the specified collection.
    """
    client = chromadb.HttpClient(host="localhost", port=8000, ssl=False)
    vector_store = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),
    )
    return vector_store

tools = []

class GeneralChatOutput(BaseModel):
    response: str
    is_finished: bool

def handle_general_query():
    
    messages = []
    
    while True:
        choice = input("Enter your query: ")
        model = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
        client = get_chroma_client(collection_name="company_kb")
        
        releted_docs = client.similarity_search_with_score(query=choice, k=3)
        context_text = "\n\n---\n\n".join(
            [f"{doc}" for doc, score in releted_docs]
        )
        
        for doc, score in releted_docs:
            print(f"[RETRIEVED DOC - {score}] {doc.page_content}")
        
        agent = create_agent(model, tools = tools, system_prompt=f"You are a food panda support agent. your task is to answer user questions based on the knowledge base and if you do not know the answer say sorry and do not make up information from your own.\n\n Context: {context_text}", response_format=GeneralChatOutput)
        
        messages.append(HumanMessage(content=choice))
        
        # response = agent.invoke({"messages": [("user", choice)]})
        response = agent.invoke({"messages": messages})
        structured_response : GeneralChatOutput = response["structured_response"]
        print(f"[AI RESPONSE]{structured_response.response}")
        
        if structured_response.is_finished:
            break

        messages.append(AIMessage(content=structured_response.response))
        

def seed_rag_kb(knowledge: str, metadata: dict):
    """
    Seeds the RAG knowledge base with general questions and answers.
    """
    client = get_chroma_client(collection_name="company_kb")
    doc_id = str(uuid4())
    doc = Document(
        page_content=knowledge, 
        metadata=metadata
    )
    client.add_documents(documents=[doc], ids=[doc_id])
    print(f"[INFO] Seeded RAG knowledge base with document ID: {doc_id} and metadata: {metadata}")
    

if __name__ == "__main__":
    # Example of seeding the RAG knowledge base
    seed_rag_kb(
        knowledge="Food Panda is a leading online food delivery service that connects users with a wide range of restaurants. We offer a seamless ordering experience, allowing customers to browse menus, place orders, and track deliveries in real-time. Our platform supports various payment methods and provides customer support for any issues related to orders, refunds, or general inquiries.",
        metadata={"category": "refund", "type": "general_question"}
    )
    seed_rag_kb(
        knowledge="Food Panda's refund turnaround time typically ranges from 5 to 7 business days. However, the exact duration may vary based on the payment method used and the specific circumstances of the  refund request. Customers are advised to check their email for confirmation and updates regarding their refund status.",
        metadata={"category": "refund", "type": "general_question"}
    )
    seed_rag_kb(
        knowledge="If you have been overcharged for your order, please contact our support team immediately. Provide your order ID and details of the issue, and we will investigate the matter. If verified, we will process a refund for the overcharged amount. Our team is committed to resolving such issues promptly.",
        metadata={"category": "overcharge", "type": "general_question"}
    )
    seed_rag_kb(
        knowledge="If you did not receive your invoice, please check your email's spam or junk folder. If it's not there, contact our support team with your order ID, and we will resend the invoice to your registered email address.",
        metadata={"category": "invoice", "type": "general_question"}
    )
    seed_rag_kb(
        knowledge="If your voucher did not apply, please ensure that the voucher code is valid and has not expired. If the issue persists, contact our support team with your order ID and voucher details, and we will assist you in resolving the issue.",
        metadata={"category": "voucher", "type": "general_question"}
    )
    seed_rag_kb(
        knowledge="If you did not receive any points for your order, please check your account to ensure that you are logged in. If the points are still missing, contact our support team with your order ID, and we will investigate the issue and credit the points to your account if applicable.",
        metadata={"category": "points", "type": "general_question"}
    )
    seed_rag_kb(
        knowledge="For any general questions or feedback regarding our services, please reach out to our support team. We value your input and strive to improve our services based on customer feedback. You can contact us through our support channels, and we will respond to your inquiries as promptly as possible. Our support contact number is 123-456-7890, and our email is support@foodpanda.com",
        metadata={"category": "general", "type": "general_question"}
    )
    
    # Start handling general queries
    print("Data seeding completed. You can now ask general questions.")
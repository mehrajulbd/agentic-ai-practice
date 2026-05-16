import os
from uuid import uuid4
from typing import List

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import chromadb

from dotenv import load_dotenv
load_dotenv()

class CompanyKnowledgeBase:
    def __init__(self, collection_name="company_policies"):
        print("⚙️ Booting up Acme Corp's AI Knowledge Base...")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        
        # cmd: chroma run
        self.client = chromadb.HttpClient(host="localhost", port=8000, ssl=False)
        
        self.vector_store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )
        
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # --- CRUD OPERATIONS FOR RAG ---
    def ingest_policy(self, content: str, dept: str, doc_name: str, page_number: int) -> str:
        """Adds a chunk of policy text to the vector database with metadata."""
        doc_id = str(uuid4())
        doc = Document(
            page_content=content, 
            metadata={"department": dept, "document": doc_name, "page": page_number}
        )
        self.vector_store.add_documents(documents=[doc], ids=[doc_id])
        return doc_id

    def update_policy(self, doc_id: str, new_content: str, dept: str, doc_name: str, page_number: int):
        """Updates an existing policy (e.g., when company rules change)."""
        doc = Document(
            page_content=new_content, 
            metadata={"department": dept, "document": doc_name, "page": page_number}
        )
        self.vector_store.update_documents(ids=[doc_id], documents=[doc])

    def delete_policy(self, doc_id: str):
        """Removes an outdated policy entirely."""
        self.vector_store.delete(ids=[doc_id])

    # --- THE CORE RAG PIPELINE ---
    def ask_assistant(self, query: str, department_filter: str = None):
        """Executes Retrieval-Augmented Generation."""
        
        print(f"\n🔍 [RETRIEVAL PHASE] Searching Vector DB for: '{query}'...")
        
        # 1. RETRIEVAL: Find similar documents, optionally filtering by metadata
        search_kwargs = {"k": 2} # Return top 2 chunks
        if department_filter:
            search_kwargs["filter"] = {"department": department_filter}
            print(f"   Applying Metadata Filter: Department = {department_filter}")

        # Fetch documents and their similarity scores (lower distance = more similar depending on metric, Langchain handles abstraction)
        docs_with_scores = self.vector_store.similarity_search_with_score(query, **search_kwargs)
        
        if not docs_with_scores:
            return "I couldn't find any relevant company policies on this topic.", []

        # Combine retrieved text chunks into a single context string
        context_text = "\n\n---\n\n".join(
            [f"Source ({doc.metadata['document']}):\n{doc.page_content}" for doc, score in docs_with_scores]
        )
        
        print(f"PREPARED CONTEXT FOR RAG: \n{context_text[:1000]}...") # Show a snippet of the context for debugging
        
        # 2. AUGMENTATION: Inject the context into the LLM's prompt
        print("🧠 [AUGMENTATION PHASE] Constructing prompt with retrieved context...")
        template = """
        You are Acme Corp's internal HR and IT assistant. 
        Answer the employee's question based strictly on the provided policy context.
        If the context does not contain the answer, politely state that you do not have that information in your knowledge base.
        Do not make up policies.
        
        CONTEXT:
        {context}
        
        EMPLOYEE QUESTION: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)
        
        # 3. GENERATION: Send the augmented prompt to the LLM
        print("✨ [GENERATION PHASE] LLM is drafting the response...")
        chain = prompt | self.llm
        response = chain.invoke({"context": context_text, "question": query})
        
        return response.content, docs_with_scores

# --- INTERACTIVE CLASSROOM SCRIPT ---
def main():
    bot = CompanyKnowledgeBase()
    
    print("\n" + "="*60)
    print("📚 INGESTING INITIAL COMPANY DOCUMENTS...")
    
    # Pre-loading the database with realistic "chunks" of data
    remote_work_id = bot.ingest_policy(
        "Acme Corp allows employees to work remotely up to 2 days per week. "
        "Employees must be in the office on Tuesdays and Thursdays. "
        "All remote days require prior approval from a direct manager.", 
        dept="HR", doc_name="Employee Handbook v1.2", page_number=12
    )
    
    it_equipment_id = bot.ingest_policy(
        "Hardware upgrades are permitted every 3 years. "
        "Standard developer issue is a MacBook Pro M3 or Dell XPS 15. "
        "Lost equipment must be reported to the IT Helpdesk within 24 hours.", 
        dept="IT", doc_name="IT Hardware Policy", page_number=None
    )
    
    expense_id = bot.ingest_policy(
        "For company travel, daily food per diem is capped at $75. "
        "Alcohol is not a reimbursable expense. Receipts are required for all transactions over $15.", 
        dept="Finance", doc_name="Travel & Expense Policy", page_number=10
    )
    
    bot.ingest_policy(
        "Employees are entitled to 15 days of paid vacation per year. "
        "Unused vacation days can be rolled over to the next year, up to a maximum of 30 days. "
        "Vacation requests must be submitted at least 2 weeks in advance.", 
        dept="HR", doc_name="Employee Handbook v1.2", page_number=20
    )
    
    bot.ingest_policy(
        "All employees must complete annual cybersecurity training. "
        "Phishing simulations will be conducted quarterly. "
        "Report any suspicious emails to the IT Security team immediately.", 
        dept="IT", doc_name="Cybersecurity Policy", page_number=None
    )
    
    bot.ingest_policy(
        "Acme Corp's code of conduct emphasizes respect, integrity, and professionalism. "
        "Harassment of any kind will not be tolerated. "
        "Employees are encouraged to report any violations to HR or use the anonymous hotline.", 
        dept="HR", doc_name="Code of Conduct", page_number=5
    )
    
    print("✅ Initial data loaded successfully.")

    while True:
        print("\n" + "="*60)
        print("ACME CORP KNOWLEDGE PORTAL - Select an action:")
        print("  [1] Ask a Question (Full Search)")
        print("  [2] Ask a Question (Filtered to IT Department)")
        print("  [3] Update Remote Work Policy (Change rules)")
        print("  [4] Delete Expense Policy")
        print("  [5] Exit")
        
        choice = input("\n👉 Enter your choice: ")

        if choice in ["1", "2"]:
            q = input("💬 Employee Question: ")
            filter_val = "IT" if choice == "2" else None
            
            answer, sources = bot.ask_assistant(q, department_filter=filter_val)
            
            print("\n" + "-"*40)
            print(f"🤖 ASSISTANT ANSWER:\n{answer}")
            print("-"*40)
            
            print("\n📊 RAG DIAGNOSTICS (What the LLM read to answer this):")
            for i, (doc, score) in enumerate(sources, 1):
                print(f"\n  Chunk {i} [Similarity: {score:.4f}]")
                print(f"  Metadata : {doc.metadata}")
                print(f"  Content  : {doc.page_content[:100]}...") # Truncate for display

        elif choice == "3":
            print("\n📈 Updating the remote work policy to be fully remote...")
            bot.update_policy(
                remote_work_id, 
                "Acme Corp is now a remote-first company. Employees may work from anywhere 5 days a week. Office attendance is optional.", 
                dept="HR", doc_name="Employee Handbook v2.0", page_number=15
            )
            print("✅ Database Updated! Try asking about remote work now.")

        elif choice == "4":
            print("\n🗑️ Deleting the Travel & Expense policy...")
            bot.delete_policy(expense_id)
            print("✅ Policy removed. Try asking about the food per diem now.")

        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
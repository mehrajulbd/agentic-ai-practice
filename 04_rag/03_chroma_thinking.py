import os
import json
from uuid import uuid4
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import chromadb

from dotenv import load_dotenv
load_dotenv()

# --- STRUCTURED OUTPUT SCHEMAS FOR REASONING ---
class QueryRewriteOutput(BaseModel):
    optimized_query: str = Field(description="The refined, standalone query optimized for vector database search.")

class ReasonerOutput(BaseModel):
    status: str = Field(description="Must be either 'CONTINUE' if more information is needed, or 'FINAL' if you can fully answer.")
    next_sub_query: Optional[str] = Field(default=None, description="The specific search query to look up next if status is CONTINUE.")
    final_answer: Optional[str] = Field(default=None, description="The complete, detailed answer to the employee's original question based strictly on context.")

class AdvancedReasoningRAG:
    def __init__(self, collection_name="advanced_company_policies"):
        print("🧠 Booting up Acme Corp's Deep Thought RAG Engine...")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        
        # cmd: chroma run
        self.client = chromadb.HttpClient(host="localhost", port=8000, ssl=False)
        
        self.vector_store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )
        
        # Using gpt-4o-mini for fast, structured reasoning decisions
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Bind structured outputs to ensure the LLM follows our execution loop control
        self.reasoner_chain = self.llm.with_structured_output(ReasonerOutput)
        self.rewrite_chain = self.llm.with_structured_output(QueryRewriteOutput)

    def ingest_policy(self, content: str, doc_name: str) -> str:
        doc_id = str(uuid4())
        doc = Document(page_content=content, metadata={"document": doc_name})
        self.vector_store.add_documents(documents=[doc], ids=[doc_id])
        return doc_id

    # --- STRATEGY 1: QUERY REWRITING ---
    def rewrite_query(self, original_query: str, history: List[str] = None) -> str:
        """Refines conversational or vague queries into optimized keywords for Vector DB lookup."""
        template = """
        You are an AI Search Optimizer. Look at the user's input and rewrite it to be an excellent, standalone vector search query.
        Strip out conversational filler ("can you tell me", "please find"). Focus on core policy concepts and nouns.
        
        Original Query: {query}
        Previous Search Context (if any): {history}
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.rewrite_chain
        result = chain.invoke({"query": original_query, "history": str(history or [])})
        return result.optimized_query

    # --- STRATEGY 2 & 3: MULTI-STEP RAG & SAFETY MECHANISMS ---
    def ask_reasoning_assistant(self, original_query: str, max_steps: int = 3):
        print(f"\n🚀 [INITIATING REASONING PIPELINE]")
        print(f"📥 Original Question: '{original_query}'")
        
        # Safety tracking sets
        visited_queries = set()
        accumulated_context = []
        search_history_log = []
        
        # 1. Initial Query Rewrite
        current_search_query = self.rewrite_query(original_query)
        print(f"🔮 [QUERY REWRITE] Optimized search vector target to: '{current_search_query}'")

        # Multi-step reasoning loop
        for step in range(1, max_steps + 1):
            print(f"\n--- 🔄 REASONING STEP {step}/{max_steps} ---")
            
            # --- SAFETY GUARD: Loop/Duplicate Query Detection ---
            if current_search_query.lower() in visited_queries:
                print(f"⚠️ [SAFETY TRIGGER] Detected circular reasoning/duplicate query loop for: '{current_search_query}'. Breaking loop.")
                break
            visited_queries.add(current_search_query.lower())

            # 2. Execution: Retrieve Data
            print(f"🔍 Searching Vector DB for: '{current_search_query}'...")
            docs_with_scores = self.vector_store.similarity_search_with_score(current_search_query, k=2)
            
            # Formulate current chunk findings
            step_context_pieces = []
            for doc, score in docs_with_scores:
                chunk_text = f"[Source: {doc.metadata['document']}] {doc.page_content}"
                if chunk_text not in accumulated_context:
                    accumulated_context.append(chunk_text)
                    step_context_pieces.append(chunk_text)
            
            search_history_log.append(f"Step {step} Query: '{current_search_query}' -> Found {len(step_context_pieces)} new insights.")

            # Compile master context for the evaluation phase
            full_context_str = "\n".join(accumulated_context)

            # 3. Evaluation: Judge adequacy & determine next steps
            reasoner_template = """
            You are Acme Corp's Executive Policy Coordinator. Your job is to answer the employee's original question by evaluating the available text blocks gathered across multiple retrieval steps.

            ORIGINAL EMPLOYEE QUESTION: {original_query}
            SEARCH HISTORY SO FAR: {history_log}
            CURRENT ACCUMULATED POLICY CONTEXT:
            {context}

            INSTRUCTIONS:
            - Determine if the accumulated context provides enough specific detail to fully and accurately answer the original question.
            - If it DOES, set status to 'FINAL' and write a detailed final_answer.
            - If it DOES NOT, and missing details are required to complete the puzzle, set status to 'CONTINUE' and formulate a precise 'next_sub_query' to look up what's missing.
            - SAFETY RULE: Do not make things up. If you look at the context and realize the information simply isn't there after trying, choose 'FINAL' and explain your limitations.
            """
            
            prompt = ChatPromptTemplate.from_template(reasoner_template)
            chain = prompt | self.reasoner_chain
            
            evaluation: ReasonerOutput = chain.invoke({
                "original_query": original_query,
                "history_log": "\n".join(search_history_log),
                "context": full_context_str
            })

            if evaluation.status == "FINAL":
                print("✨ [FINAL ANSWER GENERATED] The engine has concluded its analysis.")
                return evaluation.final_answer, accumulated_context
            
            elif evaluation.status == "CONTINUE" and evaluation.next_sub_query:
                print(f"🧠 [THINKING...] Need more info. Brainstormed next clue to find: '{evaluation.next_sub_query}'")
                # Prepare for next loop cycle
                current_search_query = self.rewrite_query(evaluation.next_sub_query, history=search_history_log)

        # --- SAFETY GUARD: Max Steps Exhausted Fallback ---
        print(f"🛑 [SAFETY TRIGGER] Reached maximum allocated reasoning depth ({max_steps} steps) without conclusion. Executing fallback summary...")
        fallback_template = """
        You ran out of reasoning steps. Synthesize the best possible answer to the employee's question using ONLY the provided context snippets.
        Be transparent about what you know and what pieces were missing.

        QUESTION: {original_query}
        CONTEXT: {context}
        """
        fallback_prompt = ChatPromptTemplate.from_template(fallback_template)
        fallback_chain = fallback_prompt | self.llm
        fallback_res = fallback_chain.invoke({"original_query": original_query, "context": "\n".join(accumulated_context)})
        
        return f"[⚠️ MAX REASONING STEPS REACHED] {fallback_res.content}", accumulated_context


# --- INTERACTIVE CLASSROOM SCRIPT ---
def main():
    bot = AdvancedReasoningRAG()
    
    print("\n" + "="*60)
    print("📚 INGESTING INTERDEPENDENT POLICIES (THE REASONING PUZZLE)...")
    
    # We purposefully scatter pieces of information across different policy documents to test multi-hop retrieval
    bot.ingest_policy(
        "To apply for an AI Special Project Stipend, an employee must follow the 'Expense Pre-Approval Workflow'. "
        "Direct manager approval is not sufficient on its own for advanced research grants.", 
        doc_name="Advanced Research Grants Policy"
    )
    
    bot.ingest_policy(
        "The Expense Pre-Approval Workflow dictates that all specialized tech requests must use Form 104-B. "
        "This application must be submitted to the Finance Architecture Board exactly 14 days before purchasing.", 
        doc_name="Expense Operations Guidelines"
    )
    
    bot.ingest_policy(
        "Form 104-B (Specialized Technology Requisition Form) is strictly hosted on the Internal Engineering Portal. "
        "It can be found listed directly underneath the 'Hardware & Grants Resources' navigation tab.", 
        doc_name="IT Systems Index"
    )
    
    bot.ingest_policy(
        "Standard company travel per-diem is managed via the Concur portal. "
        "Do not use Form 104-B for standard travel or standard developer software purchases.",
        doc_name="Travel and Entertainment Handbook"
    )

    print("✅ Interdependent data loaded successfully.")

    while True:
        print("\n" + "="*60)
        print("ACME ADVANCED REASONING PORTAL - Select an action:")
        print("  [1] Ask Complex Question (Triggers Reasoning Loops)")
        print("  [2] Run Loop-Demonstration (Tests Safety Triggers)")
        print("  [3] Exit")
        
        choice = input("\n👉 Enter your choice: ")

        if choice == "1":
            # A complex query that requires traversing through multiple pieces of documentation:
            # AI Project Stipend -> Expense Pre-Approval Workflow -> Form 104-B -> Internal Engineering Portal & 14 days rule.
            default_q = "I want to get a stipend for a new AI project. Where exactly do I find the form I need to submit, and what is the deadline?"
            print(f"\n💡 Suggestion: '{default_q}'")
            q = input("💬 Employee Question (Press Enter to use suggestion): ") or default_q
            
            answer, contexts_used = bot.ask_reasoning_assistant(q, max_steps=4)
            
            print("\n" + "-"*50)
            print(f"🤖 REASONING RAG RESPONSE:\n{answer}")
            print("-"*50)
            print(f"\n📋 Total unique documentation contexts pulled across all hops: {len(contexts_used)}")

        elif choice == "2":
            # A completely unsolvable question designed to trick regular models into infinite logic loops
            loop_q = "Can you look at the workflow rules for Form 104-B and tell me if it links to itself recursively?"
            print(f"\nRunning Safety Loop Demo on Query: '{loop_q}'")
            answer, contexts_used = bot.ask_reasoning_assistant(loop_q, max_steps=4)
            print(f"\n🤖 REASONING RAG RESPONSE:\n{answer}")

        elif choice == "3":
            print("Shutting down the engine. Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
from uuid import uuid4
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import chromadb
from dotenv import load_dotenv
load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
# client = chromadb.PersistentClient(path="./chroma_langchain_db")
client = chromadb.HttpClient(host="localhost", port=8000, ssl=False)

vector_store = Chroma(
    client=client,
    collection_name="rag_practice",
    embedding_function=embeddings,
)

# documents = [
#     Document(
#     page_content="An employee can have multiple roles in a company, such as manager, developer, and designer.",
#     metadata={"source": "tweet", "name": "Alice"},
#     id=1,
#     ),
#         Document(
#         page_content="Office day is total 5 days a week, but we can work from home on Fridays.",
#         metadata={"source": "news", "name": "Bob"},
#         id=2,
#     ),
#         Document(
#         page_content="The office is located at 123 Main Street, Anytown, USA.",
#         metadata={"source": "tweet", "name": "Charlie"},
#         id=3,
#     ),
# ]

# uuids = [str(uuid4()) for _ in range(len(documents))]
# vector_store.add_documents(documents=documents, ids=uuids)

# updated_documents = [
#     Document(
#         page_content="I had chocolate chip pancakes and fried eggs for breakfast this morning.",
#         metadata={"source": "tweet", "name": "Alice"},
#         id=1,
#     ), Document(
#         page_content="The weather forecast for tomorrow is sunny and warm, with a high of 82 degrees.",
#         metadata={"source": "news", "name": "Bob"},
#         id=2,
#     )
# ]

# vector_store.update_documents(
#     ids=uuids[:2], documents=updated_documents
# )

# vector_store.delete(ids=uuids[-1])

# results = vector_store.similarity_search(
#     "how many days is the office open?",
#     k=1,
#     # filter={"source": "tweet"},
# )
# for res in results:
#     print(f"* {res.page_content} [{res.metadata}]")
    
    
# results = vector_store.similarity_search_with_score(
#     "what are the employee roles?", k=1
#     # , filter={"source": "news"}
# )
# for res, score in results:
#     print(f"* [SIM={score:3f}] {res.page_content} [{res.metadata}]")
    
vector_embedding_value = embeddings.embed_query("what are the employee roles?")
print(f"Vector embedding value: {vector_embedding_value[:5]}...")

results = vector_store.similarity_search_by_vector(
    embedding=vector_embedding_value, k=1
)

for doc in results:
    print(f"* {doc.page_content} [{doc.metadata}]")

from langchain_text_splitters import RecursiveCharacterTextSplitter

document = """This is a long document that needs to be split into smaller chunks for processing. The RecursiveCharacterTextSplitter will help us achieve this by splitting the text based on a specified chunk size and overlap. This is a long document that needs to be split into smaller chunks for processing. The RecursiveCharacterTextSplitter will help us achieve this by splitting the text based on a specified chunk size and overlap.This is a long document that needs to be split into smaller chunks for processing. The RecursiveCharacterTextSplitter will help us achieve this by splitting the text based on a specified chunk size and overlap.


This is a long document that needs to be split into smaller chunks for processing. The RecursiveCharacterTextSplitter will help us achieve this by splitting the text based on a specified chunk size and overlap.This is a long document that needs to be split into smaller chunks for processing. The RecursiveCharacterTextSplitter will help us achieve this by splitting the text based on a specified chunk size and overlap.This is a long document that needs to be split into smaller chunks for processing. The RecursiveCharacterTextSplitter will help us achieve this by splitting the text based on a specified chunk size and overlap.


This is a long document that needs to be split into smaller chunks for processing. The RecursiveCharacterTextSplitter will help us achieve this by splitting the text based on a specified chunk size and overlap.This is a long document that needs to be split into smaller chunks for processing. The RecursiveCharacterTextSplitter will help us achieve this by splitting the text based on a specified chunk size and overlap.This is a long document that needs to be split into smaller chunks for processing. The RecursiveCharacterTextSplitter will help us achieve this by splitting the text based on a specified chunk size and overlap."""

text_splitter = RecursiveCharacterTextSplitter(chunk_size=650, chunk_overlap=0)
texts = text_splitter.split_text(document)

for i, text in enumerate(texts):
    print(f"Chunk {i+1}:\n{text}\n")
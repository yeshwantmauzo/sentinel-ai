import os
import json
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

def setup_ai_detective():
    """
    Initializes the RAG pipeline by loading the rulebook, chunking it, 
    storing it in a vector database, and connecting to Gemini.
    """
    # 1. Load the Rulebook
    # We read the plain text compliance rules we just created
    loader = TextLoader("compliance_rules.txt")
    documents = loader.load()

    # 2. Chunk the Document
    # AI models have memory limits. We break the rulebook into smaller, readable chunks.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)

    # 3. Create Embeddings (The AI's Native Language)
    # This converts our text chunks into numerical vectors so the AI can search them mathematically.
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    # 4. Build the Vector Vault (FAISS)
    # We store those numerical vectors in a blazing-fast local Meta FAISS database.
    vector_db = FAISS.from_documents(chunks, embeddings)

    # 5. Wake up the Brain (Gemini)
    # We initialize Google's Gemini Flash model. Temperature=0 makes it strictly factual, not creative.
    llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=1.0)

    # 6. Write the Prompt (The Instructions)
    # We tell the AI exactly who it is, what data it will receive, and how it must answer.
    prompt_template = """
    You are a strict financial compliance officer. Review the following transaction against the provided compliance rules.
    
    Compliance Rules:
    {context}
    
    Transaction to Evaluate:
    {question}
    
    You MUST respond with ONLY a valid JSON object. Do not add markdown blocks or conversational text.
    The JSON must have exactly two keys: 
    "status" (string: either "approved" or "flagged") 
    "fraud_score" (float: a number between 0.00 and 1.00, where 1.00 is a severe violation).
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    # 7. Chain it all together
    # This connects the Vector DB search, the Prompt, and the Gemini model into one seamless pipeline.
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(),
        return_source_documents=False,
        chain_type_kwargs={"prompt": prompt}
    )
    
    return qa_chain

# We run the setup function once when the app starts, so it's ready and waiting in memory
ai_pipeline = setup_ai_detective()

def evaluate_transaction(transaction_data: dict) -> dict:
    """
    Takes a transaction dictionary, asks the AI to evaluate it against the rules, 
    and returns the AI's JSON decision.
    """
    # We convert the Python dictionary into a string so the AI can read it
    query = str(transaction_data)
    
    # We ask the AI pipeline to evaluate the transaction!
    ai_response = ai_pipeline.invoke(query)
    
    # The AI returns a string that looks like JSON. We parse it back into a real Python dictionary.
    try:
        # Clean up the string just in case Gemini accidentally adds formatting blocks (```json)
        clean_text = ai_response['result'].replace("```json", "").replace("```", "").strip()
        decision = json.loads(clean_text)
        return decision
    except Exception as e:
        # If the AI hallucinates or fails to return JSON, we default to a safe 'flagged' status
        print(f"AI parsing error: {e}")
        return {"status": "flagged", "fraud_score": 0.99}
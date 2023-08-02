from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import aiplatform
from langchain.embeddings import TensorflowHubEmbeddings
from langchain.chat_models import ChatVertexAI
from langchain.chains import RetrievalQA

from firestore_retriever import FirestoreRetriever


app = FastAPI()

origins = [
    "*",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


model_url = "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3"
embeddings = TensorflowHubEmbeddings(model_url=model_url)


@app.get("/")
async def root():
    content = 'Retrieval Augmentation API.<br>See <a href="/docs">/docs</a>.'
    return HTMLResponse(content=content, status_code=200)


class Query(BaseModel):
    question: str
    n: int = 10


my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
    index_endpoint_name='1221803709063757824'
)

@app.post("/api/neirest_docs")
async def api(query: Query):
    vector = embeddings.embed_documents([query.question])

    neighbors = my_index_endpoint.find_neighbors(
        deployed_index_id="retreivalaugindex",
        queries=vector,
        num_neighbors=query.n
    )

    return [[neighbor.id, neighbor.distance] for neighbor in neighbors[0]]



retriever = FirestoreRetriever(
    index_endpoint_name="1221803709063757824",
    deployed_index_id="retreivalaugindex",
    collection="questions",
    embeddings = embeddings,
    top_k=1
)

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever
)

@app.post("/api/full")
async def api(query: Query):
    return qa.run(query)

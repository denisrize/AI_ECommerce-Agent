from fastapi import FastAPI

app = FastAPI(
    title="E-commerce Agent API",
    description="AI-powered e-commerce operations assistant",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "E-commerce Agent API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
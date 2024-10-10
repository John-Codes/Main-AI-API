from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load environment variables
load_dotenv()

class SearchQuery(BaseModel):
    query: str
    count: int = 10

def bing_search(query: str, count: int = 10):
    api_key = os.getenv('BING_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="BING_API_KEY not found in environment variables")
    
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "q": query,
        "count": count,
        "textFormat": "HTML"
    }
    
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error making request to Bing API: {str(e)}")

def process_results(results):
    processed = []
    for result in results.get('webPages', {}).get('value', []):
        processed.append({
            'name': result.get('name', 'No title'),
            'url': result.get('url', 'No URL'),
            'snippet': result.get('snippet', 'No snippet available')
        })
    return processed

@app.post("/search")
async def search(query: SearchQuery):
    results = bing_search(query.query, query.count)
    processed_results = process_results(results)
    
    if not processed_results:
        raise HTTPException(status_code=404, detail="No results found")
    
    return {"results": processed_results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
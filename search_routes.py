from fastapi import APIRouter, Depends, HTTPException, status
from search import bing_search, process_results
import os
from auth import Authentication, UserInDB

search_router = APIRouter(prefix="/search", tags=["search"])
auth_service = Authentication()

@search_router.get("")
async def search(query: str, current_user: UserInDB = Depends(auth_service.get_current_user)):
    try:
        if not os.getenv('BING_API_KEY'):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="BING_API_KEY not found in .env file")
        results = bing_search(query)
        processed_results = process_results(results)
        return processed_results
    except Exception as e:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

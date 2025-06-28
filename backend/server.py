from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import httpx
import asyncio
from urllib.parse import quote


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Academic Search Engine API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class Paper(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    citation_count: Optional[int] = 0
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    source: str
    paper_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SearchQuery(BaseModel):
    query: str
    author: Optional[str] = None
    venue: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    limit: Optional[int] = 20

class SearchResult(BaseModel):
    papers: List[Paper]
    total_count: int
    query_info: Dict[str, Any]

class SearchHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    result_count: int

# API Integration Functions
async def search_semantic_scholar(query: str, limit: int = 20) -> List[Dict]:
    """Search Semantic Scholar API"""
    try:
        encoded_query = quote(query)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "paperId,title,authors,abstract,year,venue,citationCount,url,openAccessPdf"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                logger.error(f"Semantic Scholar API error: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error searching Semantic Scholar: {str(e)}")
        return []

async def search_crossref(query: str, limit: int = 20) -> List[Dict]:
    """Search CrossRef API"""
    try:
        url = "https://api.crossref.org/works"
        params = {
            "query": query,
            "rows": limit,
            "select": "DOI,title,author,abstract,published-print,container-title,URL,type,is-referenced-by-count"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("items", [])
            else:
                logger.error(f"CrossRef API error: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error searching CrossRef: {str(e)}")
        return []

def parse_semantic_scholar_paper(paper_data: Dict) -> Paper:
    """Parse Semantic Scholar paper data into Paper model"""
    authors = []
    if paper_data.get("authors"):
        authors = [author.get("name", "") for author in paper_data["authors"]]
    
    pdf_url = None
    if paper_data.get("openAccessPdf"):
        pdf_url = paper_data["openAccessPdf"].get("url")
    
    return Paper(
        title=paper_data.get("title", ""),
        authors=authors,
        abstract=paper_data.get("abstract", ""),
        year=paper_data.get("year"),
        venue=paper_data.get("venue"),
        citation_count=paper_data.get("citationCount", 0),
        url=paper_data.get("url"),
        pdf_url=pdf_url,
        source="Semantic Scholar",
        paper_id=paper_data.get("paperId")
    )

def parse_crossref_paper(paper_data: Dict) -> Paper:
    """Parse CrossRef paper data into Paper model"""
    authors = []
    if paper_data.get("author"):
        authors = [f"{author.get('given', '')} {author.get('family', '')}".strip() 
                  for author in paper_data["author"]]
    
    title = ""
    if paper_data.get("title") and len(paper_data["title"]) > 0:
        title = paper_data["title"][0]
    
    year = None
    if paper_data.get("published-print", {}).get("date-parts"):
        year = paper_data["published-print"]["date-parts"][0][0]
    
    venue = ""
    if paper_data.get("container-title") and len(paper_data["container-title"]) > 0:
        venue = paper_data["container-title"][0]
    
    return Paper(
        title=title,
        authors=authors,
        abstract=paper_data.get("abstract", ""),
        year=year,
        venue=venue,
        citation_count=paper_data.get("is-referenced-by-count", 0),
        url=paper_data.get("URL"),
        doi=paper_data.get("DOI"),
        source="CrossRef"
    )

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Academic Search Engine API", "version": "1.0.0"}

@api_router.post("/search", response_model=SearchResult)
async def search_papers(search_query: SearchQuery):
    """Search for academic papers across multiple sources"""
    try:
        # Build search query
        query_parts = [search_query.query]
        if search_query.author:
            query_parts.append(f"author:{search_query.author}")
        if search_query.venue:
            query_parts.append(f"venue:{search_query.venue}")
        
        combined_query = " ".join(query_parts)
        
        # Search both APIs concurrently
        semantic_task = search_semantic_scholar(combined_query, search_query.limit // 2)
        crossref_task = search_crossref(combined_query, search_query.limit // 2)
        
        semantic_results, crossref_results = await asyncio.gather(
            semantic_task, crossref_task, return_exceptions=True
        )
        
        papers = []
        
        # Process Semantic Scholar results
        if isinstance(semantic_results, list):
            for paper_data in semantic_results:
                try:
                    paper = parse_semantic_scholar_paper(paper_data)
                    # Apply year filtering
                    if search_query.year_from and paper.year and paper.year < search_query.year_from:
                        continue
                    if search_query.year_to and paper.year and paper.year > search_query.year_to:
                        continue
                    papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing Semantic Scholar paper: {str(e)}")
        
        # Process CrossRef results
        if isinstance(crossref_results, list):
            for paper_data in crossref_results:
                try:
                    paper = parse_crossref_paper(paper_data)
                    # Apply year filtering
                    if search_query.year_from and paper.year and paper.year < search_query.year_from:
                        continue
                    if search_query.year_to and paper.year and paper.year > search_query.year_to:
                        continue
                    papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing CrossRef paper: {str(e)}")
        
        # Sort by citation count (descending)
        papers.sort(key=lambda p: p.citation_count or 0, reverse=True)
        
        # Limit results
        papers = papers[:search_query.limit]
        
        # Save search history
        history = SearchHistory(
            query=search_query.query,
            result_count=len(papers)
        )
        await db.search_history.insert_one(history.dict())
        
        # Store search results
        for paper in papers:
            await db.papers.replace_one(
                {"title": paper.title, "source": paper.source},
                paper.dict(),
                upsert=True
            )
        
        return SearchResult(
            papers=papers,
            total_count=len(papers),
            query_info={
                "query": search_query.query,
                "author": search_query.author,
                "venue": search_query.venue,
                "year_range": f"{search_query.year_from or 'any'}-{search_query.year_to or 'any'}"
            }
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@api_router.get("/search/history", response_model=List[SearchHistory])
async def get_search_history():
    """Get search history"""
    try:
        history = await db.search_history.find().sort("timestamp", -1).limit(50).to_list(50)
        return [SearchHistory(**item) for item in history]
    except Exception as e:
        logger.error(f"Error fetching search history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch search history")

@api_router.get("/papers/saved", response_model=List[Paper])
async def get_saved_papers():
    """Get saved papers from database"""
    try:
        papers = await db.papers.find().sort("created_at", -1).limit(100).to_list(100)
        return [Paper(**paper) for paper in papers]
    except Exception as e:
        logger.error(f"Error fetching saved papers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch saved papers")

@api_router.delete("/search/history")
async def clear_search_history():
    """Clear search history"""
    try:
        result = await db.search_history.delete_many({})
        return {"message": f"Deleted {result.deleted_count} search history records"}
    except Exception as e:
        logger.error(f"Error clearing search history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear search history")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
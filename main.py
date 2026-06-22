import base64
import json
import os
import logging
import traceback
import psycopg2
from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger("uvicorn")

app = FastAPI(title="Fast Product Browser API")

# Single, clean CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://anuraag696.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursor_factory=RealDictCursor
    )

# Pagination helpers
def encode_cursor(created_at: str, item_id: int) -> str:
    cursor_data = json.dumps({"c": created_at, "i": item_id})
    return base64.b64encode(cursor_data.encode()).decode()

def decode_cursor(cursor_str: str) -> tuple:
    try:
        decoded = base64.b64decode(cursor_str.encode()).decode()
        data = json.loads(decoded)
        return data["c"], data["i"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cursor format.")

# Models
class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    created_at: datetime
    updated_at: datetime

class PaginatedProducts(BaseModel):
    data: List[ProductResponse]
    next_cursor: Optional[str]
    has_more: bool

# Single API Route
@app.get("/api/products", response_model=PaginatedProducts)
def get_products(
    category: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    cursor: Optional[str] = None
):
    try:
        conn = get_db_connection()
        db_cursor = conn.cursor()
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    params = []
    conditions = []
    
    if category:
        conditions.append("category = %s")
        params.append(category)
    
    if cursor:
        cursor_created_at, cursor_id = decode_cursor(cursor)
        conditions.append("(created_at < %s OR (created_at = %s AND id < %s))")
        params.extend([cursor_created_at, cursor_created_at, cursor_id])
        
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    query = f"""
        SELECT id, name, category, price, created_at, updated_at
        FROM products
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT %s
    """
    params.append(limit + 1)
    
    try:
        db_cursor.execute(query, params)
        results = db_cursor.fetchall()
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Query failed.")
    finally:
        db_cursor.close()
        conn.close()
    
    has_more = len(results) > limit
    paginated_data = results[:limit]
    
    next_cursor = None
    if has_more and paginated_data:
        last_item = paginated_data[-1]
        next_cursor = encode_cursor(last_item['created_at'].isoformat(), last_item['id'])
        
    return {"data": paginated_data, "next_cursor": next_cursor, "has_more": has_more} 
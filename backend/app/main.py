import logging
import os
from contextlib import asynccontextmanager
from typing import List
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException, Body
from .database import get_database, close_database_connection
from .models import UserCreate, UserResponse, hash_password
from . import (
    traffic_routes,
    user_routes,
    road_traffic_routes,
    intersection_aggregation_routes,
    topology_routes,
    congestion_routes,
    signal_routes,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    logger.info("SignalIQ application starting up")
    try:
        db = get_database()
        # Verify connection
        await db.command("ping")
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
    
    yield
    
    logger.info("SignalIQ application shutting down")
    await close_database_connection()

# Create FastAPI app
app = FastAPI(
    title="SignalIQ",
    description="Intelligent Traffic Signal Management System",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include Routers
app.include_router(traffic_routes.router, prefix="/traffic", tags=["Traffic"])
app.include_router(road_traffic_routes.router, prefix="/traffic", tags=["Road Traffic"])
app.include_router(intersection_aggregation_routes.router, prefix="/traffic", tags=["Intersection Aggregation"])
app.include_router(congestion_routes.router, prefix="/traffic", tags=["Congestion"])
app.include_router(signal_routes.router, prefix="/traffic", tags=["Signal"])
app.include_router(user_routes.router, prefix="/auth", tags=["auth"])
app.include_router(topology_routes.router, prefix="/topology", tags=["Topology"])


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

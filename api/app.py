"""
FastAPI application for Study Planner
POST /plan endpoint to generate study plans
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import generate_plan
from utils.planner import get_intelligent_planner
from utils.database import get_database_manager
from utils.models import DeadlineDict

# Initialize FastAPI app
app = FastAPI(
    title="Study Planner API",
    description="Personalized ML-powered study plan generator",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response validation
class PlanRequest(BaseModel):
    """User input for plan generation"""
    tasks: List[str]
    time_spent: List[int]
    difficulty_rating: List[int]
    energy_level: int
    goals_for_tomorrow: List[str]
    available_minutes: int
    
    class Config:
        schema_extra = {
            "example": {
                "tasks": ["Math review", "ML project", "Reading"],
                "time_spent": [60, 90, 30],
                "difficulty_rating": [3, 4, 2],
                "energy_level": 4,
                "goals_for_tomorrow": ["Finish ML assignment", "Review Week 3"],
                "available_minutes": 180
            }
        }


class Metrics(BaseModel):
    """Performance metrics"""
    energy_level: int
    fatigue_score: int
    productivity_score: float
    time_pressure: float


class PlanResponse(BaseModel):
    """Generated study plan response"""
    ranked_tasks: List[str]
    recommended_minutes: List[int]
    difficulty_adjustment: int
    summary: str
    metrics: Dict[str, Any]
    deadline_recommendations: Optional[List[Dict[str, Any]]] = None
    schedule_conflicts: Optional[List[str]] = None


class DeadlineRequest(BaseModel):
    """Request to add/update a deadline"""
    title: str
    type: str  # 'assignment', 'exam', 'project', etc.
    due_date: str  # YYYY-MM-DD format
    estimated_time: int  # minutes
    description: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Math Final Exam",
                "type": "exam",
                "due_date": "2024-12-20",
                "estimated_time": 300,
                "description": "Chapters 1-10"
            }
        }


class DeadlineResponse(BaseModel):
    """Response containing deadline data"""
    id: Optional[int] = None
    title: str
    type: str
    due_date: str
    estimated_time: int
    description: Optional[str] = None
    status: str
    urgency_score: Optional[float] = None
    days_until: Optional[int] = None


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "Study Planner API"}


# Main planning endpoint
@app.post("/plan", response_model=PlanResponse)
async def create_plan(request: PlanRequest) -> Dict[str, Any]:
    """
    Generate a personalized study plan.
    
    **Request Body:**
    - tasks: List of task names
    - time_spent: List of minutes spent on each task
    - difficulty_rating: List of difficulty ratings (1-5)
    - energy_level: Current energy level (1-5)
    - goals_for_tomorrow: List of goals for tomorrow
    - available_minutes: Total available study time
    
    **Response:**
    - ranked_tasks: Tasks ranked by priority
    - recommended_minutes: Recommended time for each task
    - difficulty_adjustment: Adjustment suggestion (-1: easier, 0: same, +1: harder)
    - summary: Human-readable plan summary
    - metrics: Performance metrics
    """
    
    try:
        # Validate input
        if len(request.tasks) != len(request.time_spent):
            raise ValueError("tasks and time_spent must have same length")
        
        if len(request.tasks) != len(request.difficulty_rating):
            raise ValueError("tasks and difficulty_rating must have same length")
        
        if not (1 <= request.energy_level <= 5):
            raise ValueError("energy_level must be between 1 and 5")
        
        if request.available_minutes <= 0:
            raise ValueError("available_minutes must be positive")
        
        # Convert request to dict
        user_input = request.dict()
        
        # Generate plan
        plan = generate_plan(user_input)
        
        # Enhance with deadline intelligence
        try:
            planner = get_intelligent_planner()
            
            # Get deadline recommendations
            deadline_recommendations = planner.get_deadline_recommendations(request.available_minutes)
            if deadline_recommendations:
                plan["deadline_recommendations"] = [
                    {
                        "title": task.title,
                        "urgency_score": task.urgency_score,
                        "days_until": task.days_until,
                        "estimated_time": task.estimated_time,
                        "recommended": True
                    }
                    for task in deadline_recommendations
                ]
            
            # Detect schedule conflicts
            conflicts = planner.detect_schedule_conflicts(days_ahead=7)
            if conflicts:
                plan["schedule_conflicts"] = [
                    f"{conflict['date']}: {len(conflict['deadlines'])} deadline(s), "
                    f"estimated {conflict['total_time']} minutes"
                    for conflict in conflicts
                ]
        
        except Exception as e:
            # Log error but don't fail plan generation
            print(f"Warning: Could not enhance plan with deadlines: {e}")
        
        return plan
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail="Models not trained. Run: python models/train_models.py"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Deadline management endpoints
@app.post("/deadlines", response_model=DeadlineResponse)
async def create_deadline(request: DeadlineRequest) -> Dict[str, Any]:
    """
    Create a new deadline.
    
    **Request Body:**
    - title: Deadline title
    - type: Type of deadline (assignment, exam, project, etc.)
    - due_date: Due date in YYYY-MM-DD format
    - estimated_time: Estimated minutes needed
    - description: Optional description
    
    **Response:**
    - Created deadline with ID, status, and urgency score
    """
    try:
        db = get_database_manager()
        
        # Validate date format
        try:
            datetime.strptime(request.due_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("due_date must be in YYYY-MM-DD format")
        
        if request.estimated_time <= 0:
            raise ValueError("estimated_time must be positive")
        
        # Create deadline in database
        deadline_id = db.add_deadline(
            title=request.title,
            type=request.type,
            due_date=request.due_date,
            estimated_time=request.estimated_time,
            description=request.description or ""
        )
        
        # Calculate urgency
        planner = get_intelligent_planner()
        urgency_score = planner.calculate_urgency_score(request.due_date, request.estimated_time)
        
        # Calculate days until
        due = datetime.strptime(request.due_date, "%Y-%m-%d")
        days_until = (due - datetime.now()).days
        
        return {
            "id": deadline_id,
            "title": request.title,
            "type": request.type,
            "due_date": request.due_date,
            "estimated_time": request.estimated_time,
            "description": request.description,
            "status": "active",
            "urgency_score": round(urgency_score, 2),
            "days_until": days_until
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/deadlines")
async def list_deadlines() -> Dict[str, Any]:
    """Get all active deadlines with urgency scores."""
    try:
        db = get_database_manager()
        planner = get_intelligent_planner()
        
        deadlines = db.get_deadlines(status="active")
        
        # Add urgency scores
        enriched_deadlines = []
        for deadline in deadlines:
            urgency_score = planner.calculate_urgency_score(
                deadline["due_date"],
                deadline["estimated_time"]
            )
            due = datetime.strptime(deadline["due_date"], "%Y-%m-%d")
            days_until = (due - datetime.now()).days
            
            enriched_deadlines.append({
                **deadline,
                "urgency_score": round(urgency_score, 2),
                "days_until": days_until
            })
        
        # Sort by urgency
        enriched_deadlines.sort(key=lambda x: x["urgency_score"], reverse=True)
        
        return {
            "count": len(enriched_deadlines),
            "deadlines": enriched_deadlines
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/deadlines/recommendations/{available_minutes}")
async def get_deadline_recommendations(available_minutes: int) -> Dict[str, Any]:
    """Get deadline recommendations for available study time."""
    try:
        if available_minutes <= 0:
            raise ValueError("available_minutes must be positive")
        
        planner = get_intelligent_planner()
        recommendations = planner.get_deadline_recommendations(available_minutes)
        
        return {
            "available_minutes": available_minutes,
            "count": len(recommendations),
            "recommendations": [
                {
                    "title": task.title,
                    "urgency_score": round(task.urgency_score, 2),
                    "days_until": task.days_until,
                    "estimated_time": task.estimated_time,
                    "type": task.type
                }
                for task in recommendations
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/deadlines/conflicts/{days_ahead}")
async def detect_conflicts(days_ahead: int = 7) -> Dict[str, Any]:
    """Detect schedule conflicts in the next N days."""
    try:
        if days_ahead <= 0:
            raise ValueError("days_ahead must be positive")
        
        planner = get_intelligent_planner()
        conflicts = planner.detect_schedule_conflicts(days_ahead)
        
        return {
            "days_ahead": days_ahead,
            "conflict_count": len(conflicts),
            "conflicts": conflicts
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/deadlines/{deadline_id}/status/{new_status}")
async def update_deadline_status(deadline_id: int, new_status: str) -> Dict[str, Any]:
    """Update deadline status (active, completed, missed)."""
    try:
        valid_statuses = ["active", "completed", "missed"]
        if new_status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        db = get_database_manager()
        db.update_deadline_status(deadline_id, new_status)
        
        # Get updated deadline
        deadlines = db.get_deadlines_by_id([deadline_id])
        if not deadlines:
            raise ValueError(f"Deadline {deadline_id} not found")
        
        deadline = deadlines[0]
        planner = get_intelligent_planner()
        urgency_score = planner.calculate_urgency_score(
            deadline["due_date"],
            deadline["estimated_time"]
        )
        due = datetime.strptime(deadline["due_date"], "%Y-%m-%d")
        days_until = (due - datetime.now()).days
        
        return {
            **deadline,
            "urgency_score": round(urgency_score, 2),
            "days_until": days_until
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/deadlines/{deadline_id}/progress")
async def get_deadline_progress(deadline_id: int) -> Dict[str, Any]:
    """Get completion progress for a specific deadline."""
    try:
        planner = get_intelligent_planner()
        progress = planner.get_deadline_progress(deadline_id)
        
        return progress
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Info endpoint
@app.get("/info")
async def get_info() -> Dict[str, Any]:
    """Get API information"""
    return {
        "service": "Study Planner API",
        "version": "1.0.0",
        "endpoints": {
            "planning": {
                "/plan (POST)": "Generate study plan with deadline intelligence"
            },
            "deadline_management": {
                "/deadlines (POST)": "Create new deadline",
                "/deadlines (GET)": "List all active deadlines",
                "/deadlines/recommendations/{available_minutes} (GET)": "Get deadline recommendations",
                "/deadlines/conflicts/{days_ahead} (GET)": "Detect schedule conflicts",
                "/deadlines/{deadline_id}/status/{new_status} (PATCH)": "Update deadline status",
                "/deadlines/{deadline_id}/progress (GET)": "Get deadline progress"
            },
            "utility": {
                "/health (GET)": "Health check",
                "/info (GET)": "API information",
                "/docs (GET)": "Swagger documentation"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Study Planner API...")
    print("📚 API available at: http://localhost:8000")
    print("📖 Docs at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

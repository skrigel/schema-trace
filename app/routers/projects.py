from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.dependencies import limiter
from app.db.models import Project
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.core.auth import optional_verify_api_key

router = APIRouter(prefix="/projects", tags=["projects"])

@limiter.limit("10/minute")
@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    request: Request,
    project: ProjectCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(optional_verify_api_key)
):
    """Create a new project"""
    # Check for duplicate name
    existing = db.query(Project).filter(Project.name == project.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Project '{project.name}' already exists"
        )

    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@limiter.limit("10/minute")
@router.get("/", response_model=list[ProjectResponse])
def list_projects(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all projects with pagination"""
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects

@limiter.limit("10/minute")
@router.get("/by-name/{project_name}", response_model=ProjectResponse)
def get_project_by_name(request: Request, project_name: str, db: Session = Depends(get_db)):
    """Get a project by name (useful for CLI)"""
    project = db.query(Project).filter(Project.name == project_name).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_name}' not found"
        )
    return project

@limiter.limit("10/minute")
@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(request: Request, project_id: int, db: Session = Depends(get_db)):
    """Get a project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with id {project_id} not found"
        )
    return project

@limiter.limit("10/minute")
@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(request: Request, project_id: int, project: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project's name or description"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with id {project_id} not found"
        )

    # Update only provided fields
    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)
    return db_project

@limiter.limit("10/minute")
@router.delete("/{project_id}", status_code=204)
def delete_project(request: Request, project_id: int, db: Session = Depends(get_db)):
    """Delete a project and all its models, fields, and events"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with id {project_id} not found"
        )

    db.delete(db_project)
    db.commit()
    return None

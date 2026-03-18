from app.db.database import get_db
from app.db.models import Model, Field
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.models import ModelResponse, ModelCreate, ModelResponseWithFields, ModelUpdate
from sqlalchemy.orm import Session, joinedload


router = APIRouter(prefix="/models", tags=["models"])


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(model_id: int, db: Session = Depends(get_db)):
    """Get a model by ID (without fields)"""
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} not found")
    return model


@router.get("/{model_id}/full", response_model=ModelResponseWithFields)
def get_model_with_fields(model_id: int, include_removed: bool = False, db: Session = Depends(get_db)):
    """
    Get a model with its fields

    - **include_removed**: If True, includes removed fields (where removed_at is not None)
    """
    model = db.query(Model)\
        .options(joinedload(Model.fields))\
        .filter(Model.id == model_id)\
        .first()

    if not model:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} not found")

    # Filter to active fields only unless include_removed is True
    if not include_removed:
        model.fields = [f for f in model.fields if f.removed_at is None]

    return model


@router.get("/", response_model=list[ModelResponse])
def list_models(project_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all models, optionally filtered by project_id

    - **project_id**: Filter by project
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    query = db.query(Model)

    if project_id is not None:
        query = query.filter(Model.project_id == project_id)

    models = query.offset(skip).limit(limit).all()
    return models


@router.post("/", response_model=ModelResponse, status_code=201)
def create_model(model: ModelCreate, db: Session = Depends(get_db)):
    """Create a new model"""
    # Check if project exists
    from app.db.models import Project
    project = db.query(Project).filter(Project.id == model.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with id {model.project_id} not found")

    # Check for duplicate model name within project
    existing = db.query(Model)\
        .filter(Model.project_id == model.project_id, Model.name == model.name)\
        .first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model.name}' already exists in project {model.project_id}"
        )

    db_model = Model(**model.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


@router.patch("/{model_id}", response_model=ModelResponse)
def update_model(model_id: int, model: ModelUpdate, db: Session = Depends(get_db)):
    """Update a model's name or description"""
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} not found")

    update_data = model.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_model, field, value)

    db.commit()
    db.refresh(db_model)
    return db_model


@router.delete("/{model_id}", status_code=204)
def delete_model(model_id: int, db: Session = Depends(get_db)):
    """Delete a model and all its fields and events"""
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} not found")

    db.delete(db_model)
    db.commit()
    return None



#   1. Type safety: FastAPI validates request bodies against Pydantic schemas
#   2. Auto-generated docs: OpenAPI schema generated from Pydantic models
#   3. Separation of concerns: API structure can differ from database structure
#   4. Security: Exclude sensitive fields (passwords, internal IDs) from responses


# {
#   _id: 
#   "model": "User",
#   "fields": [
#     {
#       "name": "email",
#       "type": "varchar",
#       "nullable": false,
#       "added_at": "2024-01-12",
#       "removed_at": null
#     }
#   ]
# }
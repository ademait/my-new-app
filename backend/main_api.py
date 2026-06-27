import uvicorn
import os, json
import time as time_module
import logging
from fastapi import Depends, FastAPI, HTTPException, Request, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic_classes import *
from sql_alchemy import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

############################################
#
#   Initialize the database
#
############################################

def init_db():
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/AI_Sandbox.db")
    # Ensure local SQLite directory exists (safe no-op for other DBs)
    os.makedirs("data", exist_ok=True)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal

app = FastAPI(
    title="AI_Sandbox API",
    description="Auto-generated REST API with full CRUD operations, relationship management, and advanced features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "System", "description": "System health and statistics"},
        {"name": "User", "description": "Operations for User entities"},
        {"name": "User Relationships", "description": "Manage User relationships"},
        {"name": "LegalRequirement", "description": "Operations for LegalRequirement entities"},
        {"name": "LegalRequirement Relationships", "description": "Manage LegalRequirement relationships"},
        {"name": "AssessmentElement", "description": "Operations for AssessmentElement entities"},
        {"name": "Metric", "description": "Operations for Metric entities"},
        {"name": "Metric Relationships", "description": "Manage Metric relationships"},
        {"name": "Tool", "description": "Operations for Tool entities"},
        {"name": "Tool Relationships", "description": "Manage Tool relationships"},
        {"name": "MetricCategory", "description": "Operations for MetricCategory entities"},
        {"name": "MetricCategory Relationships", "description": "Manage MetricCategory relationships"},
        {"name": "ConfParam", "description": "Operations for ConfParam entities"},
        {"name": "ConfParam Relationships", "description": "Manage ConfParam relationships"},
        {"name": "Configuration", "description": "Operations for Configuration entities"},
        {"name": "Configuration Relationships", "description": "Manage Configuration relationships"},
        {"name": "Datashape", "description": "Operations for Datashape entities"},
        {"name": "Datashape Relationships", "description": "Manage Datashape relationships"},
        {"name": "Project", "description": "Operations for Project entities"},
        {"name": "Project Relationships", "description": "Manage Project relationships"},
        {"name": "Derived", "description": "Operations for Derived entities"},
        {"name": "Derived Relationships", "description": "Manage Derived relationships"},
        {"name": "Direct", "description": "Operations for Direct entities"},
        {"name": "Evaluation", "description": "Operations for Evaluation entities"},
        {"name": "Evaluation Relationships", "description": "Manage Evaluation relationships"},
        {"name": "Observation", "description": "Operations for Observation entities"},
        {"name": "Observation Relationships", "description": "Manage Observation relationships"},
        {"name": "Measure", "description": "Operations for Measure entities"},
        {"name": "Measure Relationships", "description": "Manage Measure relationships"},
        {"name": "Element", "description": "Operations for Element entities"},
        {"name": "Element Relationships", "description": "Manage Element relationships"},
        {"name": "Dataset", "description": "Operations for Dataset entities"},
        {"name": "Dataset Relationships", "description": "Manage Dataset relationships"},
        {"name": "Feature", "description": "Operations for Feature entities"},
        {"name": "Feature Relationships", "description": "Manage Feature relationships"},
        {"name": "AISystem", "description": "Operations for AISystem entities"},
        {"name": "AISystem Relationships", "description": "Manage AISystem relationships"},
    ]
)

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

############################################
#
#   Middleware
#
############################################

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses."""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to all responses."""
    start_time = time_module.time()
    response = await call_next(request)
    process_time = time_module.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

############################################
#
#   Exception Handlers
#
############################################

# Global exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "message": str(exc),
            "detail": "Invalid input data provided"
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors."""
    logger.error(f"Database integrity error: {exc}")

    # Extract more detailed error information
    error_detail = str(exc.orig) if hasattr(exc, 'orig') else str(exc)

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Conflict",
            "message": "Data conflict occurred",
            "detail": error_detail
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle general SQLAlchemy errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "Database operation failed",
            "detail": "An internal database error occurred"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            "message": exc.detail,
            "detail": f"HTTP {exc.status_code} error occurred"
        }
    )

# Initialize database session
SessionLocal = init_db()
# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        logger.error("Database session rollback due to exception")
        raise
    finally:
        db.close()

############################################
#
#   Global API endpoints
#
############################################

@app.get("/", tags=["System"])
def root():
    """Root endpoint - API information"""
    return {
        "name": "AI_Sandbox API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for monitoring"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }


@app.get("/statistics", tags=["System"])
def get_statistics(database: Session = Depends(get_db)):
    """Get database statistics for all entities"""
    stats = {}
    stats["user_count"] = database.query(User).count()
    stats["legalrequirement_count"] = database.query(LegalRequirement).count()
    stats["assessmentelement_count"] = database.query(AssessmentElement).count()
    stats["metric_count"] = database.query(Metric).count()
    stats["tool_count"] = database.query(Tool).count()
    stats["metriccategory_count"] = database.query(MetricCategory).count()
    stats["confparam_count"] = database.query(ConfParam).count()
    stats["configuration_count"] = database.query(Configuration).count()
    stats["datashape_count"] = database.query(Datashape).count()
    stats["project_count"] = database.query(Project).count()
    stats["derived_count"] = database.query(Derived).count()
    stats["direct_count"] = database.query(Direct).count()
    stats["evaluation_count"] = database.query(Evaluation).count()
    stats["observation_count"] = database.query(Observation).count()
    stats["measure_count"] = database.query(Measure).count()
    stats["element_count"] = database.query(Element).count()
    stats["dataset_count"] = database.query(Dataset).count()
    stats["feature_count"] = database.query(Feature).count()
    stats["aisystem_count"] = database.query(AISystem).count()
    stats["total_entities"] = sum(stats.values())
    return stats


############################################
#
#   BESSER Action Language standard lib
#
############################################


async def BAL_size(sequence:list) -> int:
    return len(sequence)

async def BAL_is_empty(sequence:list) -> bool:
    return len(sequence) == 0

async def BAL_add(sequence:list, elem) -> None:
    sequence.append(elem)

async def BAL_remove(sequence:list, elem) -> None:
    sequence.remove(elem)

async def BAL_contains(sequence:list, elem) -> bool:
    return elem in sequence

async def BAL_filter(sequence:list, predicate) -> list:
    return [elem for elem in sequence if predicate(elem)]

async def BAL_forall(sequence:list, predicate) -> bool:
    for elem in sequence:
        if not predicate(elem):
            return False
    return True

async def BAL_exists(sequence:list, predicate) -> bool:
    for elem in sequence:
        if predicate(elem):
            return True
    return False

async def BAL_one(sequence:list, predicate) -> bool:
    found = False
    for elem in sequence:
        if predicate(elem):
            if found:
                return False
            found = True
    return found

async def BAL_is_unique(sequence:list, mapping) -> bool:
    mapped = [mapping(elem) for elem in sequence]
    return len(set(mapped)) == len(mapped)

async def BAL_map(sequence:list, mapping) -> list:
    return [mapping(elem) for elem in sequence]

async def BAL_reduce(sequence:list, reduce_fn, aggregator) -> any:
    for elem in sequence:
        aggregator = reduce_fn(aggregator, elem)
    return aggregator


############################################
#
#   User functions
#
############################################

@app.get("/user/", response_model=None, tags=["User"])
def get_all_user(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(User)
        query = query.options(joinedload(User.tool))
        user_list = query.all()

        # Serialize with relationships included
        result = []
        for user_item in user_list:
            item_dict = user_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if user_item.tool:
                related_obj = user_item.tool
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['tool'] = related_dict
            else:
                item_dict['tool'] = None


            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(User).all()


@app.get("/user/count/", response_model=None, tags=["User"])
def get_count_user(database: Session = Depends(get_db)) -> dict:
    """Get the total count of User entities"""
    count = database.query(User).count()
    return {"count": count}


@app.get("/user/paginated/", response_model=None, tags=["User"])
def get_paginated_user(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of User entities"""
    total = database.query(User).count()
    user_list = database.query(User).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": user_list
    }


@app.get("/user/search/", response_model=None, tags=["User"])
def search_user(
    database: Session = Depends(get_db)
) -> list:
    """Search User entities by attributes"""
    query = database.query(User)


    results = query.all()
    return results


@app.get("/user/{user_id}/", response_model=None, tags=["User"])
async def get_user(user_id: int, database: Session = Depends(get_db)) -> User:
    db_user = database.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    response_data = {
        "user": db_user,
}
    return response_data



@app.post("/user/", response_model=None, tags=["User"])
async def create_user(user_data: UserCreate, database: Session = Depends(get_db)) -> User:

    if user_data.tool :
        db_tool = database.query(Tool).filter(Tool.id == user_data.tool).first()
        if not db_tool:
            raise HTTPException(status_code=400, detail="Tool not found")

    db_user = User(
        name=user_data.name,        tool_id=user_data.tool        )

    database.add(db_user)
    database.commit()
    database.refresh(db_user)




    return db_user


@app.post("/user/bulk/", response_model=None, tags=["User"])
async def bulk_create_user(items: list[UserCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple User entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_user = User(
                name=item_data.name,                tool_id=item_data.tool            )
            database.add(db_user)
            database.flush()  # Get ID without committing
            created_items.append(db_user.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} User entities"
    }


@app.delete("/user/bulk/", response_model=None, tags=["User"])
async def bulk_delete_user(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple User entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_user = database.query(User).filter(User.id == item_id).first()
        if db_user:
            database.delete(db_user)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} User entities"
    }

@app.put("/user/{user_id}/", response_model=None, tags=["User"])
async def update_user(user_id: int, user_data: UserCreate, database: Session = Depends(get_db)) -> User:
    db_user = database.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    setattr(db_user, 'name', user_data.name)
    if user_data.tool is not None:
        db_tool = database.query(Tool).filter(Tool.id == user_data.tool).first()
        if not db_tool:
            raise HTTPException(status_code=400, detail="Tool not found")
        setattr(db_user, 'tool_id', user_data.tool)
    else:
        setattr(db_user, 'tool_id', None)
    database.commit()
    database.refresh(db_user)

    return db_user


@app.delete("/user/{user_id}/", response_model=None, tags=["User"])
async def delete_user(user_id: int, database: Session = Depends(get_db)):
    db_user = database.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    database.delete(db_user)
    database.commit()
    return db_user






############################################
#
#   LegalRequirement functions
#
############################################

@app.get("/legalrequirement/", response_model=None, tags=["LegalRequirement"])
def get_all_legalrequirement(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(LegalRequirement)
        query = query.options(joinedload(LegalRequirement.project_1))
        legalrequirement_list = query.all()

        # Serialize with relationships included
        result = []
        for legalrequirement_item in legalrequirement_list:
            item_dict = legalrequirement_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if legalrequirement_item.project_1:
                related_obj = legalrequirement_item.project_1
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['project_1'] = related_dict
            else:
                item_dict['project_1'] = None


            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(LegalRequirement).all()


@app.get("/legalrequirement/count/", response_model=None, tags=["LegalRequirement"])
def get_count_legalrequirement(database: Session = Depends(get_db)) -> dict:
    """Get the total count of LegalRequirement entities"""
    count = database.query(LegalRequirement).count()
    return {"count": count}


@app.get("/legalrequirement/paginated/", response_model=None, tags=["LegalRequirement"])
def get_paginated_legalrequirement(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of LegalRequirement entities"""
    total = database.query(LegalRequirement).count()
    legalrequirement_list = database.query(LegalRequirement).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": legalrequirement_list
    }


@app.get("/legalrequirement/search/", response_model=None, tags=["LegalRequirement"])
def search_legalrequirement(
    database: Session = Depends(get_db)
) -> list:
    """Search LegalRequirement entities by attributes"""
    query = database.query(LegalRequirement)


    results = query.all()
    return results


@app.get("/legalrequirement/{legalrequirement_id}/", response_model=None, tags=["LegalRequirement"])
async def get_legalrequirement(legalrequirement_id: int, database: Session = Depends(get_db)) -> LegalRequirement:
    db_legalrequirement = database.query(LegalRequirement).filter(LegalRequirement.id == legalrequirement_id).first()
    if db_legalrequirement is None:
        raise HTTPException(status_code=404, detail="LegalRequirement not found")

    response_data = {
        "legalrequirement": db_legalrequirement,
}
    return response_data



@app.post("/legalrequirement/", response_model=None, tags=["LegalRequirement"])
async def create_legalrequirement(legalrequirement_data: LegalRequirementCreate, database: Session = Depends(get_db)) -> LegalRequirement:

    if legalrequirement_data.project_1 is not None:
        db_project_1 = database.query(Project).filter(Project.id == legalrequirement_data.project_1).first()
        if not db_project_1:
            raise HTTPException(status_code=400, detail="Project not found")
    else:
        raise HTTPException(status_code=400, detail="Project ID is required")

    db_legalrequirement = LegalRequirement(
        legal_ref=legalrequirement_data.legal_ref,        principle=legalrequirement_data.principle,        standard=legalrequirement_data.standard,        project_1_id=legalrequirement_data.project_1        )

    database.add(db_legalrequirement)
    database.commit()
    database.refresh(db_legalrequirement)




    return db_legalrequirement


@app.post("/legalrequirement/bulk/", response_model=None, tags=["LegalRequirement"])
async def bulk_create_legalrequirement(items: list[LegalRequirementCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple LegalRequirement entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.project_1:
                raise ValueError("Project ID is required")

            db_legalrequirement = LegalRequirement(
                legal_ref=item_data.legal_ref,                principle=item_data.principle,                standard=item_data.standard,                project_1_id=item_data.project_1            )
            database.add(db_legalrequirement)
            database.flush()  # Get ID without committing
            created_items.append(db_legalrequirement.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} LegalRequirement entities"
    }


@app.delete("/legalrequirement/bulk/", response_model=None, tags=["LegalRequirement"])
async def bulk_delete_legalrequirement(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple LegalRequirement entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_legalrequirement = database.query(LegalRequirement).filter(LegalRequirement.id == item_id).first()
        if db_legalrequirement:
            database.delete(db_legalrequirement)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} LegalRequirement entities"
    }

@app.put("/legalrequirement/{legalrequirement_id}/", response_model=None, tags=["LegalRequirement"])
async def update_legalrequirement(legalrequirement_id: int, legalrequirement_data: LegalRequirementCreate, database: Session = Depends(get_db)) -> LegalRequirement:
    db_legalrequirement = database.query(LegalRequirement).filter(LegalRequirement.id == legalrequirement_id).first()
    if db_legalrequirement is None:
        raise HTTPException(status_code=404, detail="LegalRequirement not found")

    setattr(db_legalrequirement, 'legal_ref', legalrequirement_data.legal_ref)
    setattr(db_legalrequirement, 'principle', legalrequirement_data.principle)
    setattr(db_legalrequirement, 'standard', legalrequirement_data.standard)
    if legalrequirement_data.project_1 is not None:
        db_project_1 = database.query(Project).filter(Project.id == legalrequirement_data.project_1).first()
        if not db_project_1:
            raise HTTPException(status_code=400, detail="Project not found")
        setattr(db_legalrequirement, 'project_1_id', legalrequirement_data.project_1)
    database.commit()
    database.refresh(db_legalrequirement)

    return db_legalrequirement


@app.delete("/legalrequirement/{legalrequirement_id}/", response_model=None, tags=["LegalRequirement"])
async def delete_legalrequirement(legalrequirement_id: int, database: Session = Depends(get_db)):
    db_legalrequirement = database.query(LegalRequirement).filter(LegalRequirement.id == legalrequirement_id).first()
    if db_legalrequirement is None:
        raise HTTPException(status_code=404, detail="LegalRequirement not found")
    database.delete(db_legalrequirement)
    database.commit()
    return db_legalrequirement






############################################
#
#   AssessmentElement functions
#
############################################

@app.get("/assessmentelement/", response_model=None, tags=["AssessmentElement"])
def get_all_assessmentelement(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    return database.query(AssessmentElement).all()


@app.get("/assessmentelement/count/", response_model=None, tags=["AssessmentElement"])
def get_count_assessmentelement(database: Session = Depends(get_db)) -> dict:
    """Get the total count of AssessmentElement entities"""
    count = database.query(AssessmentElement).count()
    return {"count": count}


@app.get("/assessmentelement/paginated/", response_model=None, tags=["AssessmentElement"])
def get_paginated_assessmentelement(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of AssessmentElement entities"""
    total = database.query(AssessmentElement).count()
    assessmentelement_list = database.query(AssessmentElement).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": assessmentelement_list
    }


@app.get("/assessmentelement/search/", response_model=None, tags=["AssessmentElement"])
def search_assessmentelement(
    database: Session = Depends(get_db)
) -> list:
    """Search AssessmentElement entities by attributes"""
    query = database.query(AssessmentElement)


    results = query.all()
    return results


@app.get("/assessmentelement/{assessmentelement_id}/", response_model=None, tags=["AssessmentElement"])
async def get_assessmentelement(assessmentelement_id: int, database: Session = Depends(get_db)) -> AssessmentElement:
    db_assessmentelement = database.query(AssessmentElement).filter(AssessmentElement.id == assessmentelement_id).first()
    if db_assessmentelement is None:
        raise HTTPException(status_code=404, detail="AssessmentElement not found")

    response_data = {
        "assessmentelement": db_assessmentelement,
}
    return response_data



@app.post("/assessmentelement/", response_model=None, tags=["AssessmentElement"])
async def create_assessmentelement(assessmentelement_data: AssessmentElementCreate, database: Session = Depends(get_db)) -> AssessmentElement:


    db_assessmentelement = AssessmentElement(
        name=assessmentelement_data.name,        description=assessmentelement_data.description        )

    database.add(db_assessmentelement)
    database.commit()
    database.refresh(db_assessmentelement)




    return db_assessmentelement


@app.post("/assessmentelement/bulk/", response_model=None, tags=["AssessmentElement"])
async def bulk_create_assessmentelement(items: list[AssessmentElementCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple AssessmentElement entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_assessmentelement = AssessmentElement(
                name=item_data.name,                description=item_data.description            )
            database.add(db_assessmentelement)
            database.flush()  # Get ID without committing
            created_items.append(db_assessmentelement.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} AssessmentElement entities"
    }


@app.delete("/assessmentelement/bulk/", response_model=None, tags=["AssessmentElement"])
async def bulk_delete_assessmentelement(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple AssessmentElement entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_assessmentelement = database.query(AssessmentElement).filter(AssessmentElement.id == item_id).first()
        if db_assessmentelement:
            database.delete(db_assessmentelement)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} AssessmentElement entities"
    }

@app.put("/assessmentelement/{assessmentelement_id}/", response_model=None, tags=["AssessmentElement"])
async def update_assessmentelement(assessmentelement_id: int, assessmentelement_data: AssessmentElementCreate, database: Session = Depends(get_db)) -> AssessmentElement:
    db_assessmentelement = database.query(AssessmentElement).filter(AssessmentElement.id == assessmentelement_id).first()
    if db_assessmentelement is None:
        raise HTTPException(status_code=404, detail="AssessmentElement not found")

    setattr(db_assessmentelement, 'name', assessmentelement_data.name)
    setattr(db_assessmentelement, 'description', assessmentelement_data.description)
    database.commit()
    database.refresh(db_assessmentelement)

    return db_assessmentelement


@app.delete("/assessmentelement/{assessmentelement_id}/", response_model=None, tags=["AssessmentElement"])
async def delete_assessmentelement(assessmentelement_id: int, database: Session = Depends(get_db)):
    db_assessmentelement = database.query(AssessmentElement).filter(AssessmentElement.id == assessmentelement_id).first()
    if db_assessmentelement is None:
        raise HTTPException(status_code=404, detail="AssessmentElement not found")
    database.delete(db_assessmentelement)
    database.commit()
    return db_assessmentelement






############################################
#
#   Metric functions
#
############################################

@app.get("/metric/", response_model=None, tags=["Metric"])
def get_all_metric(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Metric)
        metric_list = query.all()

        # Serialize with relationships included
        result = []
        for metric_item in metric_list:
            item_dict = metric_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            derived_list = database.query(Derived).join(derived_metric, Derived.id == derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == metric_item.id).all()
            item_dict['derivedBy'] = []
            for derived_obj in derived_list:
                derived_dict = derived_obj.__dict__.copy()
                derived_dict.pop('_sa_instance_state', None)
                item_dict['derivedBy'].append(derived_dict)
            metriccategory_list = database.query(MetricCategory).join(metriccategory_metric, MetricCategory.id == metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == metric_item.id).all()
            item_dict['category'] = []
            for metriccategory_obj in metriccategory_list:
                metriccategory_dict = metriccategory_obj.__dict__.copy()
                metriccategory_dict.pop('_sa_instance_state', None)
                item_dict['category'].append(metriccategory_dict)
            measure_list = database.query(Measure).filter(Measure.metric_id == metric_item.id).all()
            item_dict['measures'] = []
            for measure_obj in measure_list:
                measure_dict = measure_obj.__dict__.copy()
                measure_dict.pop('_sa_instance_state', None)
                item_dict['measures'].append(measure_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Metric).all()


@app.get("/metric/count/", response_model=None, tags=["Metric"])
def get_count_metric(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Metric entities"""
    count = database.query(Metric).count()
    return {"count": count}


@app.get("/metric/paginated/", response_model=None, tags=["Metric"])
def get_paginated_metric(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Metric entities"""
    total = database.query(Metric).count()
    metric_list = database.query(Metric).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": metric_list
        }

    result = []
    for metric_item in metric_list:
        derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == metric_item.id).all()
        metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == metric_item.id).all()
        measures_ids = database.query(Measure.id).filter(Measure.metric_id == metric_item.id).all()
        item_data = {
            "metric": metric_item,
            "derived_ids": [x[0] for x in derived_ids],
            "metriccategory_ids": [x[0] for x in metriccategory_ids],
            "measures_ids": [x[0] for x in measures_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/metric/search/", response_model=None, tags=["Metric"])
def search_metric(
    database: Session = Depends(get_db)
) -> list:
    """Search Metric entities by attributes"""
    query = database.query(Metric)


    results = query.all()
    return results


@app.get("/metric/{metric_id}/", response_model=None, tags=["Metric"])
async def get_metric(metric_id: int, database: Session = Depends(get_db)) -> Metric:
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == db_metric.id).all()
    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == db_metric.id).all()
    measures_ids = database.query(Measure.id).filter(Measure.metric_id == db_metric.id).all()
    response_data = {
        "metric": db_metric,
        "derived_ids": [x[0] for x in derived_ids],
        "metriccategory_ids": [x[0] for x in metriccategory_ids],
        "measures_ids": [x[0] for x in measures_ids]}
    return response_data



@app.post("/metric/", response_model=None, tags=["Metric"])
async def create_metric(metric_data: MetricCreate, database: Session = Depends(get_db)) -> Metric:

    if metric_data.derivedBy:
        for id in metric_data.derivedBy:
            # Entity already validated before creation
            db_derived = database.query(Derived).filter(Derived.id == id).first()
            if not db_derived:
                raise HTTPException(status_code=404, detail=f"Derived with ID {id} not found")
    if metric_data.category:
        for id in metric_data.category:
            # Entity already validated before creation
            db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == id).first()
            if not db_metriccategory:
                raise HTTPException(status_code=404, detail=f"MetricCategory with ID {id} not found")

    db_metric = Metric(
        name=metric_data.name,        description=metric_data.description        )

    database.add(db_metric)
    database.commit()
    database.refresh(db_metric)

    if metric_data.measures:
        # Validate that all Measure IDs exist
        for measure_id in metric_data.measures:
            db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
            if not db_measure:
                raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

        # Update the related entities with the new foreign key
        database.query(Measure).filter(Measure.id.in_(metric_data.measures)).update(
            {Measure.metric_id: db_metric.id}, synchronize_session=False
        )
        database.commit()

    if metric_data.derivedBy:
        for id in metric_data.derivedBy:
            # Entity already validated before creation
            db_derived = database.query(Derived).filter(Derived.id == id).first()
            # Create the association
            association = derived_metric.insert().values(baseMetric=db_metric.id, derivedBy=db_derived.id)
            database.execute(association)
            database.commit()
    if metric_data.category:
        for id in metric_data.category:
            # Entity already validated before creation
            db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == id).first()
            # Create the association
            association = metriccategory_metric.insert().values(metrics=db_metric.id, category=db_metriccategory.id)
            database.execute(association)
            database.commit()


    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == db_metric.id).all()
    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == db_metric.id).all()
    measures_ids = database.query(Measure.id).filter(Measure.metric_id == db_metric.id).all()
    response_data = {
        "metric": db_metric,
        "derived_ids": [x[0] for x in derived_ids],
        "metriccategory_ids": [x[0] for x in metriccategory_ids],
        "measures_ids": [x[0] for x in measures_ids]    }
    return response_data


@app.post("/metric/bulk/", response_model=None, tags=["Metric"])
async def bulk_create_metric(items: list[MetricCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Metric entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_metric = Metric(
                name=item_data.name,                description=item_data.description            )
            database.add(db_metric)
            database.flush()  # Get ID without committing
            created_items.append(db_metric.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Metric entities"
    }


@app.delete("/metric/bulk/", response_model=None, tags=["Metric"])
async def bulk_delete_metric(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Metric entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_metric = database.query(Metric).filter(Metric.id == item_id).first()
        if db_metric:
            database.delete(db_metric)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Metric entities"
    }

@app.put("/metric/{metric_id}/", response_model=None, tags=["Metric"])
async def update_metric(metric_id: int, metric_data: MetricCreate, database: Session = Depends(get_db)) -> Metric:
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    if metric_data.measures is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Measure).filter(Measure.metric_id == db_metric.id).update(
            {Measure.metric_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if metric_data.measures:
            # Validate that all IDs exist
            for measure_id in metric_data.measures:
                db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
                if not db_measure:
                    raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

            # Update the related entities with the new foreign key
            database.query(Measure).filter(Measure.id.in_(metric_data.measures)).update(
                {Measure.metric_id: db_metric.id}, synchronize_session=False
            )
    existing_derived_ids = [assoc.derivedBy for assoc in database.execute(
        derived_metric.select().where(derived_metric.c.baseMetric == db_metric.id))]

    deriveds_to_remove = set(existing_derived_ids) - set(metric_data.derivedBy)
    for derived_id in deriveds_to_remove:
        association = derived_metric.delete().where(
            (derived_metric.c.baseMetric == db_metric.id) & (derived_metric.c.derivedBy == derived_id))
        database.execute(association)

    new_derived_ids = set(metric_data.derivedBy) - set(existing_derived_ids)
    for derived_id in new_derived_ids:
        db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
        if db_derived is None:
            raise HTTPException(status_code=404, detail=f"Derived with ID {derived_id} not found")
        association = derived_metric.insert().values(derivedBy=db_derived.id, baseMetric=db_metric.id)
        database.execute(association)
    existing_metriccategory_ids = [assoc.category for assoc in database.execute(
        metriccategory_metric.select().where(metriccategory_metric.c.metrics == db_metric.id))]

    metriccategorys_to_remove = set(existing_metriccategory_ids) - set(metric_data.category)
    for metriccategory_id in metriccategorys_to_remove:
        association = metriccategory_metric.delete().where(
            (metriccategory_metric.c.metrics == db_metric.id) & (metriccategory_metric.c.category == metriccategory_id))
        database.execute(association)

    new_metriccategory_ids = set(metric_data.category) - set(existing_metriccategory_ids)
    for metriccategory_id in new_metriccategory_ids:
        db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
        if db_metriccategory is None:
            raise HTTPException(status_code=404, detail=f"MetricCategory with ID {metriccategory_id} not found")
        association = metriccategory_metric.insert().values(category=db_metriccategory.id, metrics=db_metric.id)
        database.execute(association)
    database.commit()
    database.refresh(db_metric)

    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == db_metric.id).all()
    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == db_metric.id).all()
    measures_ids = database.query(Measure.id).filter(Measure.metric_id == db_metric.id).all()
    response_data = {
        "metric": db_metric,
        "derived_ids": [x[0] for x in derived_ids],
        "metriccategory_ids": [x[0] for x in metriccategory_ids],
        "measures_ids": [x[0] for x in measures_ids]    }
    return response_data


@app.delete("/metric/{metric_id}/", response_model=None, tags=["Metric"])
async def delete_metric(metric_id: int, database: Session = Depends(get_db)):
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    database.delete(db_metric)
    database.commit()
    return db_metric

@app.post("/metric/{metric_id}/derivedBy/{derived_id}/", response_model=None, tags=["Metric Relationships"])
async def add_derivedBy_to_metric(metric_id: int, derived_id: int, database: Session = Depends(get_db)):
    """Add a Derived to this Metric's derivedBy relationship"""
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    # Check if relationship already exists
    existing = database.query(derived_metric).filter(
        (derived_metric.c.baseMetric == metric_id) &
        (derived_metric.c.derivedBy == derived_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = derived_metric.insert().values(baseMetric=metric_id, derivedBy=derived_id)
    database.execute(association)
    database.commit()

    return {"message": "Derived added to derivedBy successfully"}


@app.delete("/metric/{metric_id}/derivedBy/{derived_id}/", response_model=None, tags=["Metric Relationships"])
async def remove_derivedBy_from_metric(metric_id: int, derived_id: int, database: Session = Depends(get_db)):
    """Remove a Derived from this Metric's derivedBy relationship"""
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    # Check if relationship exists
    existing = database.query(derived_metric).filter(
        (derived_metric.c.baseMetric == metric_id) &
        (derived_metric.c.derivedBy == derived_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = derived_metric.delete().where(
        (derived_metric.c.baseMetric == metric_id) &
        (derived_metric.c.derivedBy == derived_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Derived removed from derivedBy successfully"}


@app.get("/metric/{metric_id}/derivedBy/", response_model=None, tags=["Metric Relationships"])
async def get_derivedBy_of_metric(metric_id: int, database: Session = Depends(get_db)):
    """Get all Derived entities related to this Metric through derivedBy"""
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == metric_id).all()
    derived_list = database.query(Derived).filter(Derived.id.in_([id[0] for id in derived_ids])).all()

    return {
        "metric_id": metric_id,
        "derivedBy_count": len(derived_list),
        "derivedBy": derived_list
    }

@app.post("/metric/{metric_id}/category/{metriccategory_id}/", response_model=None, tags=["Metric Relationships"])
async def add_category_to_metric(metric_id: int, metriccategory_id: int, database: Session = Depends(get_db)):
    """Add a MetricCategory to this Metric's category relationship"""
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
    if db_metriccategory is None:
        raise HTTPException(status_code=404, detail="MetricCategory not found")

    # Check if relationship already exists
    existing = database.query(metriccategory_metric).filter(
        (metriccategory_metric.c.metrics == metric_id) &
        (metriccategory_metric.c.category == metriccategory_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = metriccategory_metric.insert().values(metrics=metric_id, category=metriccategory_id)
    database.execute(association)
    database.commit()

    return {"message": "MetricCategory added to category successfully"}


@app.delete("/metric/{metric_id}/category/{metriccategory_id}/", response_model=None, tags=["Metric Relationships"])
async def remove_category_from_metric(metric_id: int, metriccategory_id: int, database: Session = Depends(get_db)):
    """Remove a MetricCategory from this Metric's category relationship"""
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    # Check if relationship exists
    existing = database.query(metriccategory_metric).filter(
        (metriccategory_metric.c.metrics == metric_id) &
        (metriccategory_metric.c.category == metriccategory_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = metriccategory_metric.delete().where(
        (metriccategory_metric.c.metrics == metric_id) &
        (metriccategory_metric.c.category == metriccategory_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "MetricCategory removed from category successfully"}


@app.get("/metric/{metric_id}/category/", response_model=None, tags=["Metric Relationships"])
async def get_category_of_metric(metric_id: int, database: Session = Depends(get_db)):
    """Get all MetricCategory entities related to this Metric through category"""
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == metric_id).all()
    metriccategory_list = database.query(MetricCategory).filter(MetricCategory.id.in_([id[0] for id in metriccategory_ids])).all()

    return {
        "metric_id": metric_id,
        "category_count": len(metriccategory_list),
        "category": metriccategory_list
    }


@app.get("/metric/{metric_id}/measures/", response_model=None, tags=["Metric Relationships"])
async def get_measures_of_metric(metric_id: int, database: Session = Depends(get_db)):
    """Get all Measure entities related to this Metric through measures"""
    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    measures_list = database.query(Measure).filter(Measure.metric_id == metric_id).all()

    return {
        "metric_id": metric_id,
        "measures_count": len(measures_list),
        "measures": measures_list
    }





############################################
#
#   Tool functions
#
############################################

@app.get("/tool/", response_model=None, tags=["Tool"])
def get_all_tool(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Tool)
        tool_list = query.all()

        # Serialize with relationships included
        result = []
        for tool_item in tool_list:
            item_dict = tool_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            observation_list = database.query(Observation).filter(Observation.tool_id == tool_item.id).all()
            item_dict['observation_1'] = []
            for observation_obj in observation_list:
                observation_dict = observation_obj.__dict__.copy()
                observation_dict.pop('_sa_instance_state', None)
                item_dict['observation_1'].append(observation_dict)
            user_list = database.query(User).filter(User.tool_id == tool_item.id).all()
            item_dict['users'] = []
            for user_obj in user_list:
                user_dict = user_obj.__dict__.copy()
                user_dict.pop('_sa_instance_state', None)
                item_dict['users'].append(user_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Tool).all()


@app.get("/tool/count/", response_model=None, tags=["Tool"])
def get_count_tool(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Tool entities"""
    count = database.query(Tool).count()
    return {"count": count}


@app.get("/tool/paginated/", response_model=None, tags=["Tool"])
def get_paginated_tool(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Tool entities"""
    total = database.query(Tool).count()
    tool_list = database.query(Tool).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": tool_list
        }

    result = []
    for tool_item in tool_list:
        observation_1_ids = database.query(Observation.id).filter(Observation.tool_id == tool_item.id).all()
        users_ids = database.query(User.id).filter(User.tool_id == tool_item.id).all()
        item_data = {
            "tool": tool_item,
            "observation_1_ids": [x[0] for x in observation_1_ids],            "users_ids": [x[0] for x in users_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/tool/search/", response_model=None, tags=["Tool"])
def search_tool(
    database: Session = Depends(get_db)
) -> list:
    """Search Tool entities by attributes"""
    query = database.query(Tool)


    results = query.all()
    return results


@app.get("/tool/{tool_id}/", response_model=None, tags=["Tool"])
async def get_tool(tool_id: int, database: Session = Depends(get_db)) -> Tool:
    db_tool = database.query(Tool).filter(Tool.id == tool_id).first()
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    observation_1_ids = database.query(Observation.id).filter(Observation.tool_id == db_tool.id).all()
    users_ids = database.query(User.id).filter(User.tool_id == db_tool.id).all()
    response_data = {
        "tool": db_tool,
        "observation_1_ids": [x[0] for x in observation_1_ids],        "users_ids": [x[0] for x in users_ids]}
    return response_data



@app.post("/tool/", response_model=None, tags=["Tool"])
async def create_tool(tool_data: ToolCreate, database: Session = Depends(get_db)) -> Tool:


    db_tool = Tool(
        name=tool_data.name,        description=tool_data.description,        target_legal_requirements=tool_data.target_legal_requirements,        project=tool_data.project,        branch=tool_data.branch,        provider=tool_data.provider,        licensing=tool_data.licensing.value,        sector=tool_data.sector.value,        target_system=tool_data.target_system.value,        verification_targets=tool_data.verification_targets.value,        scientific_reference=tool_data.scientific_reference,        verification_type=tool_data.verification_type.value,        version=tool_data.version,        project_maturity=tool_data.project_maturity        )

    database.add(db_tool)
    database.commit()
    database.refresh(db_tool)

    if tool_data.observation_1:
        # Validate that all Observation IDs exist
        for observation_id in tool_data.observation_1:
            db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
            if not db_observation:
                raise HTTPException(status_code=400, detail=f"Observation with id {observation_id} not found")

        # Update the related entities with the new foreign key
        database.query(Observation).filter(Observation.id.in_(tool_data.observation_1)).update(
            {Observation.tool_id: db_tool.id}, synchronize_session=False
        )
        database.commit()
    if tool_data.users:
        # Validate that all User IDs exist
        for user_id in tool_data.users:
            db_user = database.query(User).filter(User.id == user_id).first()
            if not db_user:
                raise HTTPException(status_code=400, detail=f"User with id {user_id} not found")

        # Update the related entities with the new foreign key
        database.query(User).filter(User.id.in_(tool_data.users)).update(
            {User.tool_id: db_tool.id}, synchronize_session=False
        )
        database.commit()



    observation_1_ids = database.query(Observation.id).filter(Observation.tool_id == db_tool.id).all()
    users_ids = database.query(User.id).filter(User.tool_id == db_tool.id).all()
    response_data = {
        "tool": db_tool,
        "observation_1_ids": [x[0] for x in observation_1_ids],        "users_ids": [x[0] for x in users_ids]    }
    return response_data


@app.post("/tool/bulk/", response_model=None, tags=["Tool"])
async def bulk_create_tool(items: list[ToolCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Tool entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_tool = Tool(
                name=item_data.name,                description=item_data.description,                target_legal_requirements=item_data.target_legal_requirements,                project=item_data.project,                branch=item_data.branch,                provider=item_data.provider,                licensing=item_data.licensing.value,                sector=item_data.sector.value,                target_system=item_data.target_system.value,                verification_targets=item_data.verification_targets.value,                scientific_reference=item_data.scientific_reference,                verification_type=item_data.verification_type.value,                version=item_data.version,                project_maturity=item_data.project_maturity            )
            database.add(db_tool)
            database.flush()  # Get ID without committing
            created_items.append(db_tool.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Tool entities"
    }


@app.delete("/tool/bulk/", response_model=None, tags=["Tool"])
async def bulk_delete_tool(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Tool entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_tool = database.query(Tool).filter(Tool.id == item_id).first()
        if db_tool:
            database.delete(db_tool)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Tool entities"
    }

@app.put("/tool/{tool_id}/", response_model=None, tags=["Tool"])
async def update_tool(tool_id: int, tool_data: ToolCreate, database: Session = Depends(get_db)) -> Tool:
    db_tool = database.query(Tool).filter(Tool.id == tool_id).first()
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    setattr(db_tool, 'target_legal_requirements', tool_data.target_legal_requirements)
    setattr(db_tool, 'project', tool_data.project)
    setattr(db_tool, 'branch', tool_data.branch)
    setattr(db_tool, 'provider', tool_data.provider)
    setattr(db_tool, 'licensing', tool_data.licensing.value)
    setattr(db_tool, 'sector', tool_data.sector.value)
    setattr(db_tool, 'target_system', tool_data.target_system.value)
    setattr(db_tool, 'verification_targets', tool_data.verification_targets.value)
    setattr(db_tool, 'scientific_reference', tool_data.scientific_reference)
    setattr(db_tool, 'verification_type', tool_data.verification_type.value)
    setattr(db_tool, 'version', tool_data.version)
    setattr(db_tool, 'project_maturity', tool_data.project_maturity)
    if tool_data.observation_1 is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Observation).filter(Observation.tool_id == db_tool.id).update(
            {Observation.tool_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if tool_data.observation_1:
            # Validate that all IDs exist
            for observation_id in tool_data.observation_1:
                db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
                if not db_observation:
                    raise HTTPException(status_code=400, detail=f"Observation with id {observation_id} not found")

            # Update the related entities with the new foreign key
            database.query(Observation).filter(Observation.id.in_(tool_data.observation_1)).update(
                {Observation.tool_id: db_tool.id}, synchronize_session=False
            )
    if tool_data.users is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(User).filter(User.tool_id == db_tool.id).update(
            {User.tool_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if tool_data.users:
            # Validate that all IDs exist
            for user_id in tool_data.users:
                db_user = database.query(User).filter(User.id == user_id).first()
                if not db_user:
                    raise HTTPException(status_code=400, detail=f"User with id {user_id} not found")

            # Update the related entities with the new foreign key
            database.query(User).filter(User.id.in_(tool_data.users)).update(
                {User.tool_id: db_tool.id}, synchronize_session=False
            )
    database.commit()
    database.refresh(db_tool)

    observation_1_ids = database.query(Observation.id).filter(Observation.tool_id == db_tool.id).all()
    users_ids = database.query(User.id).filter(User.tool_id == db_tool.id).all()
    response_data = {
        "tool": db_tool,
        "observation_1_ids": [x[0] for x in observation_1_ids],        "users_ids": [x[0] for x in users_ids]    }
    return response_data


@app.delete("/tool/{tool_id}/", response_model=None, tags=["Tool"])
async def delete_tool(tool_id: int, database: Session = Depends(get_db)):
    db_tool = database.query(Tool).filter(Tool.id == tool_id).first()
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    database.delete(db_tool)
    database.commit()
    return db_tool


@app.get("/tool/{tool_id}/observation_1/", response_model=None, tags=["Tool Relationships"])
async def get_observation_1_of_tool(tool_id: int, database: Session = Depends(get_db)):
    """Get all Observation entities related to this Tool through observation_1"""
    db_tool = database.query(Tool).filter(Tool.id == tool_id).first()
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    observation_1_list = database.query(Observation).filter(Observation.tool_id == tool_id).all()

    return {
        "tool_id": tool_id,
        "observation_1_count": len(observation_1_list),
        "observation_1": observation_1_list
    }

@app.get("/tool/{tool_id}/users/", response_model=None, tags=["Tool Relationships"])
async def get_users_of_tool(tool_id: int, database: Session = Depends(get_db)):
    """Get all User entities related to this Tool through users"""
    db_tool = database.query(Tool).filter(Tool.id == tool_id).first()
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    users_list = database.query(User).filter(User.tool_id == tool_id).all()

    return {
        "tool_id": tool_id,
        "users_count": len(users_list),
        "users": users_list
    }





############################################
#
#   MetricCategory functions
#
############################################

@app.get("/metriccategory/", response_model=None, tags=["MetricCategory"])
def get_all_metriccategory(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(MetricCategory)
        metriccategory_list = query.all()

        # Serialize with relationships included
        result = []
        for metriccategory_item in metriccategory_list:
            item_dict = metriccategory_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            metric_list = database.query(Metric).join(metriccategory_metric, Metric.id == metriccategory_metric.c.metrics).filter(metriccategory_metric.c.category == metriccategory_item.id).all()
            item_dict['metrics'] = []
            for metric_obj in metric_list:
                metric_dict = metric_obj.__dict__.copy()
                metric_dict.pop('_sa_instance_state', None)
                item_dict['metrics'].append(metric_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(MetricCategory).all()


@app.get("/metriccategory/count/", response_model=None, tags=["MetricCategory"])
def get_count_metriccategory(database: Session = Depends(get_db)) -> dict:
    """Get the total count of MetricCategory entities"""
    count = database.query(MetricCategory).count()
    return {"count": count}


@app.get("/metriccategory/paginated/", response_model=None, tags=["MetricCategory"])
def get_paginated_metriccategory(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of MetricCategory entities"""
    total = database.query(MetricCategory).count()
    metriccategory_list = database.query(MetricCategory).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": metriccategory_list
        }

    result = []
    for metriccategory_item in metriccategory_list:
        metric_ids = database.query(metriccategory_metric.c.metrics).filter(metriccategory_metric.c.category == metriccategory_item.id).all()
        item_data = {
            "metriccategory": metriccategory_item,
            "metric_ids": [x[0] for x in metric_ids],
        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/metriccategory/search/", response_model=None, tags=["MetricCategory"])
def search_metriccategory(
    database: Session = Depends(get_db)
) -> list:
    """Search MetricCategory entities by attributes"""
    query = database.query(MetricCategory)


    results = query.all()
    return results


@app.get("/metriccategory/{metriccategory_id}/", response_model=None, tags=["MetricCategory"])
async def get_metriccategory(metriccategory_id: int, database: Session = Depends(get_db)) -> MetricCategory:
    db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
    if db_metriccategory is None:
        raise HTTPException(status_code=404, detail="MetricCategory not found")

    metric_ids = database.query(metriccategory_metric.c.metrics).filter(metriccategory_metric.c.category == db_metriccategory.id).all()
    response_data = {
        "metriccategory": db_metriccategory,
        "metric_ids": [x[0] for x in metric_ids],
}
    return response_data



@app.post("/metriccategory/", response_model=None, tags=["MetricCategory"])
async def create_metriccategory(metriccategory_data: MetricCategoryCreate, database: Session = Depends(get_db)) -> MetricCategory:

    if metriccategory_data.metrics:
        for id in metriccategory_data.metrics:
            # Entity already validated before creation
            db_metric = database.query(Metric).filter(Metric.id == id).first()
            if not db_metric:
                raise HTTPException(status_code=404, detail=f"Metric with ID {id} not found")

    db_metriccategory = MetricCategory(
        name=metriccategory_data.name,        description=metriccategory_data.description        )

    database.add(db_metriccategory)
    database.commit()
    database.refresh(db_metriccategory)


    if metriccategory_data.metrics:
        for id in metriccategory_data.metrics:
            # Entity already validated before creation
            db_metric = database.query(Metric).filter(Metric.id == id).first()
            # Create the association
            association = metriccategory_metric.insert().values(category=db_metriccategory.id, metrics=db_metric.id)
            database.execute(association)
            database.commit()


    metric_ids = database.query(metriccategory_metric.c.metrics).filter(metriccategory_metric.c.category == db_metriccategory.id).all()
    response_data = {
        "metriccategory": db_metriccategory,
        "metric_ids": [x[0] for x in metric_ids],
    }
    return response_data


@app.post("/metriccategory/bulk/", response_model=None, tags=["MetricCategory"])
async def bulk_create_metriccategory(items: list[MetricCategoryCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple MetricCategory entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_metriccategory = MetricCategory(
                name=item_data.name,                description=item_data.description            )
            database.add(db_metriccategory)
            database.flush()  # Get ID without committing
            created_items.append(db_metriccategory.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} MetricCategory entities"
    }


@app.delete("/metriccategory/bulk/", response_model=None, tags=["MetricCategory"])
async def bulk_delete_metriccategory(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple MetricCategory entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == item_id).first()
        if db_metriccategory:
            database.delete(db_metriccategory)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} MetricCategory entities"
    }

@app.put("/metriccategory/{metriccategory_id}/", response_model=None, tags=["MetricCategory"])
async def update_metriccategory(metriccategory_id: int, metriccategory_data: MetricCategoryCreate, database: Session = Depends(get_db)) -> MetricCategory:
    db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
    if db_metriccategory is None:
        raise HTTPException(status_code=404, detail="MetricCategory not found")

    existing_metric_ids = [assoc.metrics for assoc in database.execute(
        metriccategory_metric.select().where(metriccategory_metric.c.category == db_metriccategory.id))]

    metrics_to_remove = set(existing_metric_ids) - set(metriccategory_data.metrics)
    for metric_id in metrics_to_remove:
        association = metriccategory_metric.delete().where(
            (metriccategory_metric.c.category == db_metriccategory.id) & (metriccategory_metric.c.metrics == metric_id))
        database.execute(association)

    new_metric_ids = set(metriccategory_data.metrics) - set(existing_metric_ids)
    for metric_id in new_metric_ids:
        db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
        if db_metric is None:
            raise HTTPException(status_code=404, detail=f"Metric with ID {metric_id} not found")
        association = metriccategory_metric.insert().values(metrics=db_metric.id, category=db_metriccategory.id)
        database.execute(association)
    database.commit()
    database.refresh(db_metriccategory)

    metric_ids = database.query(metriccategory_metric.c.metrics).filter(metriccategory_metric.c.category == db_metriccategory.id).all()
    response_data = {
        "metriccategory": db_metriccategory,
        "metric_ids": [x[0] for x in metric_ids],
    }
    return response_data


@app.delete("/metriccategory/{metriccategory_id}/", response_model=None, tags=["MetricCategory"])
async def delete_metriccategory(metriccategory_id: int, database: Session = Depends(get_db)):
    db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
    if db_metriccategory is None:
        raise HTTPException(status_code=404, detail="MetricCategory not found")
    database.delete(db_metriccategory)
    database.commit()
    return db_metriccategory

@app.post("/metriccategory/{metriccategory_id}/metrics/{metric_id}/", response_model=None, tags=["MetricCategory Relationships"])
async def add_metrics_to_metriccategory(metriccategory_id: int, metric_id: int, database: Session = Depends(get_db)):
    """Add a Metric to this MetricCategory's metrics relationship"""
    db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
    if db_metriccategory is None:
        raise HTTPException(status_code=404, detail="MetricCategory not found")

    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    # Check if relationship already exists
    existing = database.query(metriccategory_metric).filter(
        (metriccategory_metric.c.category == metriccategory_id) &
        (metriccategory_metric.c.metrics == metric_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = metriccategory_metric.insert().values(category=metriccategory_id, metrics=metric_id)
    database.execute(association)
    database.commit()

    return {"message": "Metric added to metrics successfully"}


@app.delete("/metriccategory/{metriccategory_id}/metrics/{metric_id}/", response_model=None, tags=["MetricCategory Relationships"])
async def remove_metrics_from_metriccategory(metriccategory_id: int, metric_id: int, database: Session = Depends(get_db)):
    """Remove a Metric from this MetricCategory's metrics relationship"""
    db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
    if db_metriccategory is None:
        raise HTTPException(status_code=404, detail="MetricCategory not found")

    # Check if relationship exists
    existing = database.query(metriccategory_metric).filter(
        (metriccategory_metric.c.category == metriccategory_id) &
        (metriccategory_metric.c.metrics == metric_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = metriccategory_metric.delete().where(
        (metriccategory_metric.c.category == metriccategory_id) &
        (metriccategory_metric.c.metrics == metric_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Metric removed from metrics successfully"}


@app.get("/metriccategory/{metriccategory_id}/metrics/", response_model=None, tags=["MetricCategory Relationships"])
async def get_metrics_of_metriccategory(metriccategory_id: int, database: Session = Depends(get_db)):
    """Get all Metric entities related to this MetricCategory through metrics"""
    db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
    if db_metriccategory is None:
        raise HTTPException(status_code=404, detail="MetricCategory not found")

    metric_ids = database.query(metriccategory_metric.c.metrics).filter(metriccategory_metric.c.category == metriccategory_id).all()
    metric_list = database.query(Metric).filter(Metric.id.in_([id[0] for id in metric_ids])).all()

    return {
        "metriccategory_id": metriccategory_id,
        "metrics_count": len(metric_list),
        "metrics": metric_list
    }






############################################
#
#   ConfParam functions
#
############################################

@app.get("/confparam/", response_model=None, tags=["ConfParam"])
def get_all_confparam(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(ConfParam)
        query = query.options(joinedload(ConfParam.conf))
        confparam_list = query.all()

        # Serialize with relationships included
        result = []
        for confparam_item in confparam_list:
            item_dict = confparam_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if confparam_item.conf:
                related_obj = confparam_item.conf
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['conf'] = related_dict
            else:
                item_dict['conf'] = None


            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(ConfParam).all()


@app.get("/confparam/count/", response_model=None, tags=["ConfParam"])
def get_count_confparam(database: Session = Depends(get_db)) -> dict:
    """Get the total count of ConfParam entities"""
    count = database.query(ConfParam).count()
    return {"count": count}


@app.get("/confparam/paginated/", response_model=None, tags=["ConfParam"])
def get_paginated_confparam(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of ConfParam entities"""
    total = database.query(ConfParam).count()
    confparam_list = database.query(ConfParam).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": confparam_list
    }


@app.get("/confparam/search/", response_model=None, tags=["ConfParam"])
def search_confparam(
    database: Session = Depends(get_db)
) -> list:
    """Search ConfParam entities by attributes"""
    query = database.query(ConfParam)


    results = query.all()
    return results


@app.get("/confparam/{confparam_id}/", response_model=None, tags=["ConfParam"])
async def get_confparam(confparam_id: int, database: Session = Depends(get_db)) -> ConfParam:
    db_confparam = database.query(ConfParam).filter(ConfParam.id == confparam_id).first()
    if db_confparam is None:
        raise HTTPException(status_code=404, detail="ConfParam not found")

    response_data = {
        "confparam": db_confparam,
}
    return response_data



@app.post("/confparam/", response_model=None, tags=["ConfParam"])
async def create_confparam(confparam_data: ConfParamCreate, database: Session = Depends(get_db)) -> ConfParam:

    if confparam_data.conf is not None:
        db_conf = database.query(Configuration).filter(Configuration.id == confparam_data.conf).first()
        if not db_conf:
            raise HTTPException(status_code=400, detail="Configuration not found")
    else:
        raise HTTPException(status_code=400, detail="Configuration ID is required")

    db_confparam = ConfParam(
        name=confparam_data.name,        description=confparam_data.description,        value=confparam_data.value,        param_type=confparam_data.param_type,        conf_id=confparam_data.conf        )

    database.add(db_confparam)
    database.commit()
    database.refresh(db_confparam)




    return db_confparam


@app.post("/confparam/bulk/", response_model=None, tags=["ConfParam"])
async def bulk_create_confparam(items: list[ConfParamCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple ConfParam entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.conf:
                raise ValueError("Configuration ID is required")

            db_confparam = ConfParam(
                name=item_data.name,                description=item_data.description,                value=item_data.value,                param_type=item_data.param_type,                conf_id=item_data.conf            )
            database.add(db_confparam)
            database.flush()  # Get ID without committing
            created_items.append(db_confparam.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} ConfParam entities"
    }


@app.delete("/confparam/bulk/", response_model=None, tags=["ConfParam"])
async def bulk_delete_confparam(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple ConfParam entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_confparam = database.query(ConfParam).filter(ConfParam.id == item_id).first()
        if db_confparam:
            database.delete(db_confparam)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} ConfParam entities"
    }

@app.put("/confparam/{confparam_id}/", response_model=None, tags=["ConfParam"])
async def update_confparam(confparam_id: int, confparam_data: ConfParamCreate, database: Session = Depends(get_db)) -> ConfParam:
    db_confparam = database.query(ConfParam).filter(ConfParam.id == confparam_id).first()
    if db_confparam is None:
        raise HTTPException(status_code=404, detail="ConfParam not found")

    setattr(db_confparam, 'value', confparam_data.value)
    setattr(db_confparam, 'param_type', confparam_data.param_type)
    if confparam_data.conf is not None:
        db_conf = database.query(Configuration).filter(Configuration.id == confparam_data.conf).first()
        if not db_conf:
            raise HTTPException(status_code=400, detail="Configuration not found")
        setattr(db_confparam, 'conf_id', confparam_data.conf)
    database.commit()
    database.refresh(db_confparam)

    return db_confparam


@app.delete("/confparam/{confparam_id}/", response_model=None, tags=["ConfParam"])
async def delete_confparam(confparam_id: int, database: Session = Depends(get_db)):
    db_confparam = database.query(ConfParam).filter(ConfParam.id == confparam_id).first()
    if db_confparam is None:
        raise HTTPException(status_code=404, detail="ConfParam not found")
    database.delete(db_confparam)
    database.commit()
    return db_confparam






############################################
#
#   Configuration functions
#
############################################

@app.get("/configuration/", response_model=None, tags=["Configuration"])
def get_all_configuration(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Configuration)
        configuration_list = query.all()

        # Serialize with relationships included
        result = []
        for configuration_item in configuration_list:
            item_dict = configuration_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            confparam_list = database.query(ConfParam).filter(ConfParam.conf_id == configuration_item.id).all()
            item_dict['params'] = []
            for confparam_obj in confparam_list:
                confparam_dict = confparam_obj.__dict__.copy()
                confparam_dict.pop('_sa_instance_state', None)
                item_dict['params'].append(confparam_dict)
            evaluation_list = database.query(Evaluation).filter(Evaluation.config_id == configuration_item.id).all()
            item_dict['eval'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['eval'].append(evaluation_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Configuration).all()


@app.get("/configuration/count/", response_model=None, tags=["Configuration"])
def get_count_configuration(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Configuration entities"""
    count = database.query(Configuration).count()
    return {"count": count}


@app.get("/configuration/paginated/", response_model=None, tags=["Configuration"])
def get_paginated_configuration(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Configuration entities"""
    total = database.query(Configuration).count()
    configuration_list = database.query(Configuration).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": configuration_list
        }

    result = []
    for configuration_item in configuration_list:
        params_ids = database.query(ConfParam.id).filter(ConfParam.conf_id == configuration_item.id).all()
        eval_ids = database.query(Evaluation.id).filter(Evaluation.config_id == configuration_item.id).all()
        item_data = {
            "configuration": configuration_item,
            "params_ids": [x[0] for x in params_ids],            "eval_ids": [x[0] for x in eval_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/configuration/search/", response_model=None, tags=["Configuration"])
def search_configuration(
    database: Session = Depends(get_db)
) -> list:
    """Search Configuration entities by attributes"""
    query = database.query(Configuration)


    results = query.all()
    return results


@app.get("/configuration/{configuration_id}/", response_model=None, tags=["Configuration"])
async def get_configuration(configuration_id: int, database: Session = Depends(get_db)) -> Configuration:
    db_configuration = database.query(Configuration).filter(Configuration.id == configuration_id).first()
    if db_configuration is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    params_ids = database.query(ConfParam.id).filter(ConfParam.conf_id == db_configuration.id).all()
    eval_ids = database.query(Evaluation.id).filter(Evaluation.config_id == db_configuration.id).all()
    response_data = {
        "configuration": db_configuration,
        "params_ids": [x[0] for x in params_ids],        "eval_ids": [x[0] for x in eval_ids]}
    return response_data



@app.post("/configuration/", response_model=None, tags=["Configuration"])
async def create_configuration(configuration_data: ConfigurationCreate, database: Session = Depends(get_db)) -> Configuration:


    db_configuration = Configuration(
        name=configuration_data.name,        description=configuration_data.description        )

    database.add(db_configuration)
    database.commit()
    database.refresh(db_configuration)

    if configuration_data.params:
        # Validate that all ConfParam IDs exist
        for confparam_id in configuration_data.params:
            db_confparam = database.query(ConfParam).filter(ConfParam.id == confparam_id).first()
            if not db_confparam:
                raise HTTPException(status_code=400, detail=f"ConfParam with id {confparam_id} not found")

        # Update the related entities with the new foreign key
        database.query(ConfParam).filter(ConfParam.id.in_(configuration_data.params)).update(
            {ConfParam.conf_id: db_configuration.id}, synchronize_session=False
        )
        database.commit()
    if configuration_data.eval:
        # Validate that all Evaluation IDs exist
        for evaluation_id in configuration_data.eval:
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not db_evaluation:
                raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

        # Update the related entities with the new foreign key
        database.query(Evaluation).filter(Evaluation.id.in_(configuration_data.eval)).update(
            {Evaluation.config_id: db_configuration.id}, synchronize_session=False
        )
        database.commit()



    params_ids = database.query(ConfParam.id).filter(ConfParam.conf_id == db_configuration.id).all()
    eval_ids = database.query(Evaluation.id).filter(Evaluation.config_id == db_configuration.id).all()
    response_data = {
        "configuration": db_configuration,
        "params_ids": [x[0] for x in params_ids],        "eval_ids": [x[0] for x in eval_ids]    }
    return response_data


@app.post("/configuration/bulk/", response_model=None, tags=["Configuration"])
async def bulk_create_configuration(items: list[ConfigurationCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Configuration entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_configuration = Configuration(
                name=item_data.name,                description=item_data.description            )
            database.add(db_configuration)
            database.flush()  # Get ID without committing
            created_items.append(db_configuration.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Configuration entities"
    }


@app.delete("/configuration/bulk/", response_model=None, tags=["Configuration"])
async def bulk_delete_configuration(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Configuration entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_configuration = database.query(Configuration).filter(Configuration.id == item_id).first()
        if db_configuration:
            database.delete(db_configuration)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Configuration entities"
    }

@app.put("/configuration/{configuration_id}/", response_model=None, tags=["Configuration"])
async def update_configuration(configuration_id: int, configuration_data: ConfigurationCreate, database: Session = Depends(get_db)) -> Configuration:
    db_configuration = database.query(Configuration).filter(Configuration.id == configuration_id).first()
    if db_configuration is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    if configuration_data.params is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(ConfParam).filter(ConfParam.conf_id == db_configuration.id).update(
            {ConfParam.conf_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if configuration_data.params:
            # Validate that all IDs exist
            for confparam_id in configuration_data.params:
                db_confparam = database.query(ConfParam).filter(ConfParam.id == confparam_id).first()
                if not db_confparam:
                    raise HTTPException(status_code=400, detail=f"ConfParam with id {confparam_id} not found")

            # Update the related entities with the new foreign key
            database.query(ConfParam).filter(ConfParam.id.in_(configuration_data.params)).update(
                {ConfParam.conf_id: db_configuration.id}, synchronize_session=False
            )
    if configuration_data.eval is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Evaluation).filter(Evaluation.config_id == db_configuration.id).update(
            {Evaluation.config_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if configuration_data.eval:
            # Validate that all IDs exist
            for evaluation_id in configuration_data.eval:
                db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
                if not db_evaluation:
                    raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

            # Update the related entities with the new foreign key
            database.query(Evaluation).filter(Evaluation.id.in_(configuration_data.eval)).update(
                {Evaluation.config_id: db_configuration.id}, synchronize_session=False
            )
    database.commit()
    database.refresh(db_configuration)

    params_ids = database.query(ConfParam.id).filter(ConfParam.conf_id == db_configuration.id).all()
    eval_ids = database.query(Evaluation.id).filter(Evaluation.config_id == db_configuration.id).all()
    response_data = {
        "configuration": db_configuration,
        "params_ids": [x[0] for x in params_ids],        "eval_ids": [x[0] for x in eval_ids]    }
    return response_data


@app.delete("/configuration/{configuration_id}/", response_model=None, tags=["Configuration"])
async def delete_configuration(configuration_id: int, database: Session = Depends(get_db)):
    db_configuration = database.query(Configuration).filter(Configuration.id == configuration_id).first()
    if db_configuration is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    database.delete(db_configuration)
    database.commit()
    return db_configuration


@app.get("/configuration/{configuration_id}/params/", response_model=None, tags=["Configuration Relationships"])
async def get_params_of_configuration(configuration_id: int, database: Session = Depends(get_db)):
    """Get all ConfParam entities related to this Configuration through params"""
    db_configuration = database.query(Configuration).filter(Configuration.id == configuration_id).first()
    if db_configuration is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    params_list = database.query(ConfParam).filter(ConfParam.conf_id == configuration_id).all()

    return {
        "configuration_id": configuration_id,
        "params_count": len(params_list),
        "params": params_list
    }

@app.get("/configuration/{configuration_id}/eval/", response_model=None, tags=["Configuration Relationships"])
async def get_eval_of_configuration(configuration_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this Configuration through eval"""
    db_configuration = database.query(Configuration).filter(Configuration.id == configuration_id).first()
    if db_configuration is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    eval_list = database.query(Evaluation).filter(Evaluation.config_id == configuration_id).all()

    return {
        "configuration_id": configuration_id,
        "eval_count": len(eval_list),
        "eval": eval_list
    }





############################################
#
#   Datashape functions
#
############################################

@app.get("/datashape/", response_model=None, tags=["Datashape"])
def get_all_datashape(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Datashape)
        datashape_list = query.all()

        # Serialize with relationships included
        result = []
        for datashape_item in datashape_list:
            item_dict = datashape_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            feature_list = database.query(Feature).join(datashape_feature, Feature.id == datashape_feature.c.f_date).filter(datashape_feature.c.date == datashape_item.id).all()
            item_dict['f_date'] = []
            for feature_obj in feature_list:
                feature_dict = feature_obj.__dict__.copy()
                feature_dict.pop('_sa_instance_state', None)
                item_dict['f_date'].append(feature_dict)
            feature_list = database.query(Feature).filter(Feature.features_id == datashape_item.id).all()
            item_dict['f_features'] = []
            for feature_obj in feature_list:
                feature_dict = feature_obj.__dict__.copy()
                feature_dict.pop('_sa_instance_state', None)
                item_dict['f_features'].append(feature_dict)
            dataset_list = database.query(Dataset).filter(Dataset.datashape_id == datashape_item.id).all()
            item_dict['dataset_1'] = []
            for dataset_obj in dataset_list:
                dataset_dict = dataset_obj.__dict__.copy()
                dataset_dict.pop('_sa_instance_state', None)
                item_dict['dataset_1'].append(dataset_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Datashape).all()


@app.get("/datashape/count/", response_model=None, tags=["Datashape"])
def get_count_datashape(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Datashape entities"""
    count = database.query(Datashape).count()
    return {"count": count}


@app.get("/datashape/paginated/", response_model=None, tags=["Datashape"])
def get_paginated_datashape(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Datashape entities"""
    total = database.query(Datashape).count()
    datashape_list = database.query(Datashape).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": datashape_list
        }

    result = []
    for datashape_item in datashape_list:
        feature_ids = database.query(datashape_feature.c.f_date).filter(datashape_feature.c.date == datashape_item.id).all()
        f_features_ids = database.query(Feature.id).filter(Feature.features_id == datashape_item.id).all()
        dataset_1_ids = database.query(Dataset.id).filter(Dataset.datashape_id == datashape_item.id).all()
        item_data = {
            "datashape": datashape_item,
            "feature_ids": [x[0] for x in feature_ids],
            "f_features_ids": [x[0] for x in f_features_ids],            "dataset_1_ids": [x[0] for x in dataset_1_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/datashape/search/", response_model=None, tags=["Datashape"])
def search_datashape(
    database: Session = Depends(get_db)
) -> list:
    """Search Datashape entities by attributes"""
    query = database.query(Datashape)


    results = query.all()
    return results


@app.get("/datashape/{datashape_id}/", response_model=None, tags=["Datashape"])
async def get_datashape(datashape_id: int, database: Session = Depends(get_db)) -> Datashape:
    db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
    if db_datashape is None:
        raise HTTPException(status_code=404, detail="Datashape not found")

    feature_ids = database.query(datashape_feature.c.f_date).filter(datashape_feature.c.date == db_datashape.id).all()
    f_features_ids = database.query(Feature.id).filter(Feature.features_id == db_datashape.id).all()
    dataset_1_ids = database.query(Dataset.id).filter(Dataset.datashape_id == db_datashape.id).all()
    response_data = {
        "datashape": db_datashape,
        "feature_ids": [x[0] for x in feature_ids],
        "f_features_ids": [x[0] for x in f_features_ids],        "dataset_1_ids": [x[0] for x in dataset_1_ids]}
    return response_data



@app.post("/datashape/", response_model=None, tags=["Datashape"])
async def create_datashape(datashape_data: DatashapeCreate, database: Session = Depends(get_db)) -> Datashape:

    if datashape_data.f_date:
        for id in datashape_data.f_date:
            # Entity already validated before creation
            db_feature = database.query(Feature).filter(Feature.id == id).first()
            if not db_feature:
                raise HTTPException(status_code=404, detail=f"Feature with ID {id} not found")

    db_datashape = Datashape(
        accepted_target_values=datashape_data.accepted_target_values        )

    database.add(db_datashape)
    database.commit()
    database.refresh(db_datashape)

    if datashape_data.f_features:
        # Validate that all Feature IDs exist
        for feature_id in datashape_data.f_features:
            db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
            if not db_feature:
                raise HTTPException(status_code=400, detail=f"Feature with id {feature_id} not found")

        # Update the related entities with the new foreign key
        database.query(Feature).filter(Feature.id.in_(datashape_data.f_features)).update(
            {Feature.features_id: db_datashape.id}, synchronize_session=False
        )
        database.commit()
    if datashape_data.dataset_1:
        # Validate that all Dataset IDs exist
        for dataset_id in datashape_data.dataset_1:
            db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not db_dataset:
                raise HTTPException(status_code=400, detail=f"Dataset with id {dataset_id} not found")

        # Update the related entities with the new foreign key
        database.query(Dataset).filter(Dataset.id.in_(datashape_data.dataset_1)).update(
            {Dataset.datashape_id: db_datashape.id}, synchronize_session=False
        )
        database.commit()

    if datashape_data.f_date:
        for id in datashape_data.f_date:
            # Entity already validated before creation
            db_feature = database.query(Feature).filter(Feature.id == id).first()
            # Create the association
            association = datashape_feature.insert().values(date=db_datashape.id, f_date=db_feature.id)
            database.execute(association)
            database.commit()


    feature_ids = database.query(datashape_feature.c.f_date).filter(datashape_feature.c.date == db_datashape.id).all()
    f_features_ids = database.query(Feature.id).filter(Feature.features_id == db_datashape.id).all()
    dataset_1_ids = database.query(Dataset.id).filter(Dataset.datashape_id == db_datashape.id).all()
    response_data = {
        "datashape": db_datashape,
        "feature_ids": [x[0] for x in feature_ids],
        "f_features_ids": [x[0] for x in f_features_ids],        "dataset_1_ids": [x[0] for x in dataset_1_ids]    }
    return response_data


@app.post("/datashape/bulk/", response_model=None, tags=["Datashape"])
async def bulk_create_datashape(items: list[DatashapeCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Datashape entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_datashape = Datashape(
                accepted_target_values=item_data.accepted_target_values            )
            database.add(db_datashape)
            database.flush()  # Get ID without committing
            created_items.append(db_datashape.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Datashape entities"
    }


@app.delete("/datashape/bulk/", response_model=None, tags=["Datashape"])
async def bulk_delete_datashape(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Datashape entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_datashape = database.query(Datashape).filter(Datashape.id == item_id).first()
        if db_datashape:
            database.delete(db_datashape)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Datashape entities"
    }

@app.put("/datashape/{datashape_id}/", response_model=None, tags=["Datashape"])
async def update_datashape(datashape_id: int, datashape_data: DatashapeCreate, database: Session = Depends(get_db)) -> Datashape:
    db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
    if db_datashape is None:
        raise HTTPException(status_code=404, detail="Datashape not found")

    setattr(db_datashape, 'accepted_target_values', datashape_data.accepted_target_values)
    if datashape_data.f_features is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Feature).filter(Feature.features_id == db_datashape.id).update(
            {Feature.features_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if datashape_data.f_features:
            # Validate that all IDs exist
            for feature_id in datashape_data.f_features:
                db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
                if not db_feature:
                    raise HTTPException(status_code=400, detail=f"Feature with id {feature_id} not found")

            # Update the related entities with the new foreign key
            database.query(Feature).filter(Feature.id.in_(datashape_data.f_features)).update(
                {Feature.features_id: db_datashape.id}, synchronize_session=False
            )
    if datashape_data.dataset_1 is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Dataset).filter(Dataset.datashape_id == db_datashape.id).update(
            {Dataset.datashape_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if datashape_data.dataset_1:
            # Validate that all IDs exist
            for dataset_id in datashape_data.dataset_1:
                db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
                if not db_dataset:
                    raise HTTPException(status_code=400, detail=f"Dataset with id {dataset_id} not found")

            # Update the related entities with the new foreign key
            database.query(Dataset).filter(Dataset.id.in_(datashape_data.dataset_1)).update(
                {Dataset.datashape_id: db_datashape.id}, synchronize_session=False
            )
    existing_feature_ids = [assoc.f_date for assoc in database.execute(
        datashape_feature.select().where(datashape_feature.c.date == db_datashape.id))]

    features_to_remove = set(existing_feature_ids) - set(datashape_data.f_date)
    for feature_id in features_to_remove:
        association = datashape_feature.delete().where(
            (datashape_feature.c.date == db_datashape.id) & (datashape_feature.c.f_date == feature_id))
        database.execute(association)

    new_feature_ids = set(datashape_data.f_date) - set(existing_feature_ids)
    for feature_id in new_feature_ids:
        db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
        if db_feature is None:
            raise HTTPException(status_code=404, detail=f"Feature with ID {feature_id} not found")
        association = datashape_feature.insert().values(f_date=db_feature.id, date=db_datashape.id)
        database.execute(association)
    database.commit()
    database.refresh(db_datashape)

    feature_ids = database.query(datashape_feature.c.f_date).filter(datashape_feature.c.date == db_datashape.id).all()
    f_features_ids = database.query(Feature.id).filter(Feature.features_id == db_datashape.id).all()
    dataset_1_ids = database.query(Dataset.id).filter(Dataset.datashape_id == db_datashape.id).all()
    response_data = {
        "datashape": db_datashape,
        "feature_ids": [x[0] for x in feature_ids],
        "f_features_ids": [x[0] for x in f_features_ids],        "dataset_1_ids": [x[0] for x in dataset_1_ids]    }
    return response_data


@app.delete("/datashape/{datashape_id}/", response_model=None, tags=["Datashape"])
async def delete_datashape(datashape_id: int, database: Session = Depends(get_db)):
    db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
    if db_datashape is None:
        raise HTTPException(status_code=404, detail="Datashape not found")
    database.delete(db_datashape)
    database.commit()
    return db_datashape

@app.post("/datashape/{datashape_id}/f_date/{feature_id}/", response_model=None, tags=["Datashape Relationships"])
async def add_f_date_to_datashape(datashape_id: int, feature_id: int, database: Session = Depends(get_db)):
    """Add a Feature to this Datashape's f_date relationship"""
    db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
    if db_datashape is None:
        raise HTTPException(status_code=404, detail="Datashape not found")

    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Check if relationship already exists
    existing = database.query(datashape_feature).filter(
        (datashape_feature.c.date == datashape_id) &
        (datashape_feature.c.f_date == feature_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = datashape_feature.insert().values(date=datashape_id, f_date=feature_id)
    database.execute(association)
    database.commit()

    return {"message": "Feature added to f_date successfully"}


@app.delete("/datashape/{datashape_id}/f_date/{feature_id}/", response_model=None, tags=["Datashape Relationships"])
async def remove_f_date_from_datashape(datashape_id: int, feature_id: int, database: Session = Depends(get_db)):
    """Remove a Feature from this Datashape's f_date relationship"""
    db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
    if db_datashape is None:
        raise HTTPException(status_code=404, detail="Datashape not found")

    # Check if relationship exists
    existing = database.query(datashape_feature).filter(
        (datashape_feature.c.date == datashape_id) &
        (datashape_feature.c.f_date == feature_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = datashape_feature.delete().where(
        (datashape_feature.c.date == datashape_id) &
        (datashape_feature.c.f_date == feature_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Feature removed from f_date successfully"}


@app.get("/datashape/{datashape_id}/f_date/", response_model=None, tags=["Datashape Relationships"])
async def get_f_date_of_datashape(datashape_id: int, database: Session = Depends(get_db)):
    """Get all Feature entities related to this Datashape through f_date"""
    db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
    if db_datashape is None:
        raise HTTPException(status_code=404, detail="Datashape not found")

    feature_ids = database.query(datashape_feature.c.f_date).filter(datashape_feature.c.date == datashape_id).all()
    feature_list = database.query(Feature).filter(Feature.id.in_([id[0] for id in feature_ids])).all()

    return {
        "datashape_id": datashape_id,
        "f_date_count": len(feature_list),
        "f_date": feature_list
    }


@app.get("/datashape/{datashape_id}/f_features/", response_model=None, tags=["Datashape Relationships"])
async def get_f_features_of_datashape(datashape_id: int, database: Session = Depends(get_db)):
    """Get all Feature entities related to this Datashape through f_features"""
    db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
    if db_datashape is None:
        raise HTTPException(status_code=404, detail="Datashape not found")

    f_features_list = database.query(Feature).filter(Feature.features_id == datashape_id).all()

    return {
        "datashape_id": datashape_id,
        "f_features_count": len(f_features_list),
        "f_features": f_features_list
    }

@app.get("/datashape/{datashape_id}/dataset_1/", response_model=None, tags=["Datashape Relationships"])
async def get_dataset_1_of_datashape(datashape_id: int, database: Session = Depends(get_db)):
    """Get all Dataset entities related to this Datashape through dataset_1"""
    db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
    if db_datashape is None:
        raise HTTPException(status_code=404, detail="Datashape not found")

    dataset_1_list = database.query(Dataset).filter(Dataset.datashape_id == datashape_id).all()

    return {
        "datashape_id": datashape_id,
        "dataset_1_count": len(dataset_1_list),
        "dataset_1": dataset_1_list
    }





############################################
#
#   Project functions
#
############################################

@app.get("/project/", response_model=None, tags=["Project"])
def get_all_project(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Project)
        project_list = query.all()

        # Serialize with relationships included
        result = []
        for project_item in project_list:
            item_dict = project_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            evaluation_list = database.query(Evaluation).filter(Evaluation.project_id == project_item.id).all()
            item_dict['eval'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['eval'].append(evaluation_dict)
            legalrequirement_list = database.query(LegalRequirement).filter(LegalRequirement.project_1_id == project_item.id).all()
            item_dict['legal_requirements'] = []
            for legalrequirement_obj in legalrequirement_list:
                legalrequirement_dict = legalrequirement_obj.__dict__.copy()
                legalrequirement_dict.pop('_sa_instance_state', None)
                item_dict['legal_requirements'].append(legalrequirement_dict)
            element_list = database.query(Element).filter(Element.project_id == project_item.id).all()
            item_dict['involves'] = []
            for element_obj in element_list:
                element_dict = element_obj.__dict__.copy()
                element_dict.pop('_sa_instance_state', None)
                item_dict['involves'].append(element_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Project).all()


@app.get("/project/count/", response_model=None, tags=["Project"])
def get_count_project(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Project entities"""
    count = database.query(Project).count()
    return {"count": count}


@app.get("/project/paginated/", response_model=None, tags=["Project"])
def get_paginated_project(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Project entities"""
    total = database.query(Project).count()
    project_list = database.query(Project).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": project_list
        }

    result = []
    for project_item in project_list:
        eval_ids = database.query(Evaluation.id).filter(Evaluation.project_id == project_item.id).all()
        legal_requirements_ids = database.query(LegalRequirement.id).filter(LegalRequirement.project_1_id == project_item.id).all()
        involves_ids = database.query(Element.id).filter(Element.project_id == project_item.id).all()
        item_data = {
            "project": project_item,
            "eval_ids": [x[0] for x in eval_ids],            "legal_requirements_ids": [x[0] for x in legal_requirements_ids],            "involves_ids": [x[0] for x in involves_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/project/search/", response_model=None, tags=["Project"])
def search_project(
    database: Session = Depends(get_db)
) -> list:
    """Search Project entities by attributes"""
    query = database.query(Project)


    results = query.all()
    return results


@app.get("/project/{project_id}/", response_model=None, tags=["Project"])
async def get_project(project_id: int, database: Session = Depends(get_db)) -> Project:
    db_project = database.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    eval_ids = database.query(Evaluation.id).filter(Evaluation.project_id == db_project.id).all()
    legal_requirements_ids = database.query(LegalRequirement.id).filter(LegalRequirement.project_1_id == db_project.id).all()
    involves_ids = database.query(Element.id).filter(Element.project_id == db_project.id).all()
    response_data = {
        "project": db_project,
        "eval_ids": [x[0] for x in eval_ids],        "legal_requirements_ids": [x[0] for x in legal_requirements_ids],        "involves_ids": [x[0] for x in involves_ids]}
    return response_data



@app.post("/project/", response_model=None, tags=["Project"])
async def create_project(project_data: ProjectCreate, database: Session = Depends(get_db)) -> Project:


    db_project = Project(
        name=project_data.name,        status=project_data.status.value        )

    database.add(db_project)
    database.commit()
    database.refresh(db_project)

    if project_data.eval:
        # Validate that all Evaluation IDs exist
        for evaluation_id in project_data.eval:
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not db_evaluation:
                raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

        # Update the related entities with the new foreign key
        database.query(Evaluation).filter(Evaluation.id.in_(project_data.eval)).update(
            {Evaluation.project_id: db_project.id}, synchronize_session=False
        )
        database.commit()
    if project_data.legal_requirements:
        # Validate that all LegalRequirement IDs exist
        for legalrequirement_id in project_data.legal_requirements:
            db_legalrequirement = database.query(LegalRequirement).filter(LegalRequirement.id == legalrequirement_id).first()
            if not db_legalrequirement:
                raise HTTPException(status_code=400, detail=f"LegalRequirement with id {legalrequirement_id} not found")

        # Update the related entities with the new foreign key
        database.query(LegalRequirement).filter(LegalRequirement.id.in_(project_data.legal_requirements)).update(
            {LegalRequirement.project_1_id: db_project.id}, synchronize_session=False
        )
        database.commit()
    if project_data.involves:
        # Validate that all Element IDs exist
        for element_id in project_data.involves:
            db_element = database.query(Element).filter(Element.id == element_id).first()
            if not db_element:
                raise HTTPException(status_code=400, detail=f"Element with id {element_id} not found")

        # Update the related entities with the new foreign key
        database.query(Element).filter(Element.id.in_(project_data.involves)).update(
            {Element.project_id: db_project.id}, synchronize_session=False
        )
        database.commit()



    eval_ids = database.query(Evaluation.id).filter(Evaluation.project_id == db_project.id).all()
    legal_requirements_ids = database.query(LegalRequirement.id).filter(LegalRequirement.project_1_id == db_project.id).all()
    involves_ids = database.query(Element.id).filter(Element.project_id == db_project.id).all()
    response_data = {
        "project": db_project,
        "eval_ids": [x[0] for x in eval_ids],        "legal_requirements_ids": [x[0] for x in legal_requirements_ids],        "involves_ids": [x[0] for x in involves_ids]    }
    return response_data


@app.post("/project/bulk/", response_model=None, tags=["Project"])
async def bulk_create_project(items: list[ProjectCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Project entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_project = Project(
                name=item_data.name,                status=item_data.status.value            )
            database.add(db_project)
            database.flush()  # Get ID without committing
            created_items.append(db_project.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Project entities"
    }


@app.delete("/project/bulk/", response_model=None, tags=["Project"])
async def bulk_delete_project(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Project entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_project = database.query(Project).filter(Project.id == item_id).first()
        if db_project:
            database.delete(db_project)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Project entities"
    }

@app.put("/project/{project_id}/", response_model=None, tags=["Project"])
async def update_project(project_id: int, project_data: ProjectCreate, database: Session = Depends(get_db)) -> Project:
    db_project = database.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    setattr(db_project, 'name', project_data.name)
    setattr(db_project, 'status', project_data.status.value)
    if project_data.eval is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Evaluation).filter(Evaluation.project_id == db_project.id).update(
            {Evaluation.project_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if project_data.eval:
            # Validate that all IDs exist
            for evaluation_id in project_data.eval:
                db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
                if not db_evaluation:
                    raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

            # Update the related entities with the new foreign key
            database.query(Evaluation).filter(Evaluation.id.in_(project_data.eval)).update(
                {Evaluation.project_id: db_project.id}, synchronize_session=False
            )
    if project_data.legal_requirements is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(LegalRequirement).filter(LegalRequirement.project_1_id == db_project.id).update(
            {LegalRequirement.project_1_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if project_data.legal_requirements:
            # Validate that all IDs exist
            for legalrequirement_id in project_data.legal_requirements:
                db_legalrequirement = database.query(LegalRequirement).filter(LegalRequirement.id == legalrequirement_id).first()
                if not db_legalrequirement:
                    raise HTTPException(status_code=400, detail=f"LegalRequirement with id {legalrequirement_id} not found")

            # Update the related entities with the new foreign key
            database.query(LegalRequirement).filter(LegalRequirement.id.in_(project_data.legal_requirements)).update(
                {LegalRequirement.project_1_id: db_project.id}, synchronize_session=False
            )
    if project_data.involves is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Element).filter(Element.project_id == db_project.id).update(
            {Element.project_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if project_data.involves:
            # Validate that all IDs exist
            for element_id in project_data.involves:
                db_element = database.query(Element).filter(Element.id == element_id).first()
                if not db_element:
                    raise HTTPException(status_code=400, detail=f"Element with id {element_id} not found")

            # Update the related entities with the new foreign key
            database.query(Element).filter(Element.id.in_(project_data.involves)).update(
                {Element.project_id: db_project.id}, synchronize_session=False
            )
    database.commit()
    database.refresh(db_project)

    eval_ids = database.query(Evaluation.id).filter(Evaluation.project_id == db_project.id).all()
    legal_requirements_ids = database.query(LegalRequirement.id).filter(LegalRequirement.project_1_id == db_project.id).all()
    involves_ids = database.query(Element.id).filter(Element.project_id == db_project.id).all()
    response_data = {
        "project": db_project,
        "eval_ids": [x[0] for x in eval_ids],        "legal_requirements_ids": [x[0] for x in legal_requirements_ids],        "involves_ids": [x[0] for x in involves_ids]    }
    return response_data


@app.delete("/project/{project_id}/", response_model=None, tags=["Project"])
async def delete_project(project_id: int, database: Session = Depends(get_db)):
    db_project = database.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    database.delete(db_project)
    database.commit()
    return db_project


@app.get("/project/{project_id}/eval/", response_model=None, tags=["Project Relationships"])
async def get_eval_of_project(project_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this Project through eval"""
    db_project = database.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    eval_list = database.query(Evaluation).filter(Evaluation.project_id == project_id).all()

    return {
        "project_id": project_id,
        "eval_count": len(eval_list),
        "eval": eval_list
    }

@app.get("/project/{project_id}/legal_requirements/", response_model=None, tags=["Project Relationships"])
async def get_legal_requirements_of_project(project_id: int, database: Session = Depends(get_db)):
    """Get all LegalRequirement entities related to this Project through legal_requirements"""
    db_project = database.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    legal_requirements_list = database.query(LegalRequirement).filter(LegalRequirement.project_1_id == project_id).all()

    return {
        "project_id": project_id,
        "legal_requirements_count": len(legal_requirements_list),
        "legal_requirements": legal_requirements_list
    }

@app.get("/project/{project_id}/involves/", response_model=None, tags=["Project Relationships"])
async def get_involves_of_project(project_id: int, database: Session = Depends(get_db)):
    """Get all Element entities related to this Project through involves"""
    db_project = database.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    involves_list = database.query(Element).filter(Element.project_id == project_id).all()

    return {
        "project_id": project_id,
        "involves_count": len(involves_list),
        "involves": involves_list
    }





############################################
#
#   Derived functions
#
############################################

@app.get("/derived/", response_model=None, tags=["Derived"])
def get_all_derived(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Derived)
        derived_list = query.all()

        # Serialize with relationships included
        result = []
        for derived_item in derived_list:
            item_dict = derived_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            metric_list = database.query(Metric).join(derived_metric, Metric.id == derived_metric.c.baseMetric).filter(derived_metric.c.derivedBy == derived_item.id).all()
            item_dict['baseMetric'] = []
            for metric_obj in metric_list:
                metric_dict = metric_obj.__dict__.copy()
                metric_dict.pop('_sa_instance_state', None)
                item_dict['baseMetric'].append(metric_dict)
            derived_list = database.query(Derived).join(derived_metric, Derived.id == derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == derived_item.id).all()
            item_dict['derivedBy'] = []
            for derived_obj in derived_list:
                derived_dict = derived_obj.__dict__.copy()
                derived_dict.pop('_sa_instance_state', None)
                item_dict['derivedBy'].append(derived_dict)
            metriccategory_list = database.query(MetricCategory).join(metriccategory_metric, MetricCategory.id == metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == derived_item.id).all()
            item_dict['category'] = []
            for metriccategory_obj in metriccategory_list:
                metriccategory_dict = metriccategory_obj.__dict__.copy()
                metriccategory_dict.pop('_sa_instance_state', None)
                item_dict['category'].append(metriccategory_dict)
            measure_list = database.query(Measure).filter(Measure.metric_id == derived_item.id).all()
            item_dict['measures'] = []
            for measure_obj in measure_list:
                measure_dict = measure_obj.__dict__.copy()
                measure_dict.pop('_sa_instance_state', None)
                item_dict['measures'].append(measure_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Derived).all()


@app.get("/derived/count/", response_model=None, tags=["Derived"])
def get_count_derived(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Derived entities"""
    count = database.query(Derived).count()
    return {"count": count}


@app.get("/derived/paginated/", response_model=None, tags=["Derived"])
def get_paginated_derived(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Derived entities"""
    total = database.query(Derived).count()
    derived_list = database.query(Derived).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": derived_list
        }

    result = []
    for derived_item in derived_list:
        metric_ids = database.query(derived_metric.c.baseMetric).filter(derived_metric.c.derivedBy == derived_item.id).all()
        derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == derived_item.id).all()
        metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == derived_item.id).all()
        measures_ids = database.query(Measure.id).filter(Measure.metric_id == derived_item.id).all()
        item_data = {
            "derived": derived_item,
            "metric_ids": [x[0] for x in metric_ids],
            "derived_ids": [x[0] for x in derived_ids],
            "metriccategory_ids": [x[0] for x in metriccategory_ids],
            "measures_ids": [x[0] for x in measures_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/derived/search/", response_model=None, tags=["Derived"])
def search_derived(
    database: Session = Depends(get_db)
) -> list:
    """Search Derived entities by attributes"""
    query = database.query(Derived)


    results = query.all()
    return results


@app.get("/derived/{derived_id}/", response_model=None, tags=["Derived"])
async def get_derived(derived_id: int, database: Session = Depends(get_db)) -> Derived:
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    metric_ids = database.query(derived_metric.c.baseMetric).filter(derived_metric.c.derivedBy == db_derived.id).all()
    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == db_derived.id).all()
    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == db_derived.id).all()
    measures_ids = database.query(Measure.id).filter(Measure.metric_id == db_derived.id).all()
    response_data = {
        "derived": db_derived,
        "metric_ids": [x[0] for x in metric_ids],
        "derived_ids": [x[0] for x in derived_ids],
        "metriccategory_ids": [x[0] for x in metriccategory_ids],
        "measures_ids": [x[0] for x in measures_ids]}
    return response_data



@app.post("/derived/", response_model=None, tags=["Derived"])
async def create_derived(derived_data: DerivedCreate, database: Session = Depends(get_db)) -> Derived:

    if not derived_data.baseMetric or len(derived_data.baseMetric) < 1:
        raise HTTPException(status_code=400, detail="At least 1 Metric(s) required")
    if derived_data.baseMetric:
        for id in derived_data.baseMetric:
            # Entity already validated before creation
            db_metric = database.query(Metric).filter(Metric.id == id).first()
            if not db_metric:
                raise HTTPException(status_code=404, detail=f"Metric with ID {id} not found")
    if derived_data.derivedBy:
        for id in derived_data.derivedBy:
            # Entity already validated before creation
            db_derived = database.query(Derived).filter(Derived.id == id).first()
            if not db_derived:
                raise HTTPException(status_code=404, detail=f"Derived with ID {id} not found")
    if derived_data.category:
        for id in derived_data.category:
            # Entity already validated before creation
            db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == id).first()
            if not db_metriccategory:
                raise HTTPException(status_code=404, detail=f"MetricCategory with ID {id} not found")

    db_derived = Derived(
        name=derived_data.name,        description=derived_data.description,        expression=derived_data.expression        )

    database.add(db_derived)
    database.commit()
    database.refresh(db_derived)

    if derived_data.measures:
        # Validate that all Measure IDs exist
        for measure_id in derived_data.measures:
            db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
            if not db_measure:
                raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

        # Update the related entities with the new foreign key
        database.query(Measure).filter(Measure.id.in_(derived_data.measures)).update(
            {Measure.metric_id: db_derived.id}, synchronize_session=False
        )
        database.commit()

    if derived_data.baseMetric:
        for id in derived_data.baseMetric:
            # Entity already validated before creation
            db_metric = database.query(Metric).filter(Metric.id == id).first()
            # Create the association
            association = derived_metric.insert().values(derivedBy=db_derived.id, baseMetric=db_metric.id)
            database.execute(association)
            database.commit()
    if derived_data.derivedBy:
        for id in derived_data.derivedBy:
            # Entity already validated before creation
            db_derived = database.query(Derived).filter(Derived.id == id).first()
            # Create the association
            association = derived_metric.insert().values(baseMetric=db_derived.id, derivedBy=db_derived.id)
            database.execute(association)
            database.commit()
    if derived_data.category:
        for id in derived_data.category:
            # Entity already validated before creation
            db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == id).first()
            # Create the association
            association = metriccategory_metric.insert().values(metrics=db_derived.id, category=db_metriccategory.id)
            database.execute(association)
            database.commit()


    metric_ids = database.query(derived_metric.c.baseMetric).filter(derived_metric.c.derivedBy == db_derived.id).all()
    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == db_derived.id).all()
    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == db_derived.id).all()
    measures_ids = database.query(Measure.id).filter(Measure.metric_id == db_derived.id).all()
    response_data = {
        "derived": db_derived,
        "metric_ids": [x[0] for x in metric_ids],
        "derived_ids": [x[0] for x in derived_ids],
        "metriccategory_ids": [x[0] for x in metriccategory_ids],
        "measures_ids": [x[0] for x in measures_ids]    }
    return response_data


@app.post("/derived/bulk/", response_model=None, tags=["Derived"])
async def bulk_create_derived(items: list[DerivedCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Derived entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_derived = Derived(
                name=item_data.name,                description=item_data.description,                expression=item_data.expression            )
            database.add(db_derived)
            database.flush()  # Get ID without committing
            created_items.append(db_derived.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Derived entities"
    }


@app.delete("/derived/bulk/", response_model=None, tags=["Derived"])
async def bulk_delete_derived(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Derived entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_derived = database.query(Derived).filter(Derived.id == item_id).first()
        if db_derived:
            database.delete(db_derived)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Derived entities"
    }

@app.put("/derived/{derived_id}/", response_model=None, tags=["Derived"])
async def update_derived(derived_id: int, derived_data: DerivedCreate, database: Session = Depends(get_db)) -> Derived:
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    setattr(db_derived, 'expression', derived_data.expression)
    if derived_data.measures is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Measure).filter(Measure.metric_id == db_derived.id).update(
            {Measure.metric_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if derived_data.measures:
            # Validate that all IDs exist
            for measure_id in derived_data.measures:
                db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
                if not db_measure:
                    raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

            # Update the related entities with the new foreign key
            database.query(Measure).filter(Measure.id.in_(derived_data.measures)).update(
                {Measure.metric_id: db_derived.id}, synchronize_session=False
            )
    existing_metric_ids = [assoc.baseMetric for assoc in database.execute(
        derived_metric.select().where(derived_metric.c.derivedBy == db_derived.id))]

    metrics_to_remove = set(existing_metric_ids) - set(derived_data.baseMetric)
    for metric_id in metrics_to_remove:
        association = derived_metric.delete().where(
            (derived_metric.c.derivedBy == db_derived.id) & (derived_metric.c.baseMetric == metric_id))
        database.execute(association)

    new_metric_ids = set(derived_data.baseMetric) - set(existing_metric_ids)
    for metric_id in new_metric_ids:
        db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
        if db_metric is None:
            raise HTTPException(status_code=404, detail=f"Metric with ID {metric_id} not found")
        association = derived_metric.insert().values(baseMetric=db_metric.id, derivedBy=db_derived.id)
        database.execute(association)
    existing_derived_ids = [assoc.derivedBy for assoc in database.execute(
        derived_metric.select().where(derived_metric.c.baseMetric == db_derived.id))]

    deriveds_to_remove = set(existing_derived_ids) - set(derived_data.derivedBy)
    for derived_id in deriveds_to_remove:
        association = derived_metric.delete().where(
            (derived_metric.c.baseMetric == db_derived.id) & (derived_metric.c.derivedBy == derived_id))
        database.execute(association)

    new_derived_ids = set(derived_data.derivedBy) - set(existing_derived_ids)
    for derived_id in new_derived_ids:
        db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
        if db_derived is None:
            raise HTTPException(status_code=404, detail=f"Derived with ID {derived_id} not found")
        association = derived_metric.insert().values(derivedBy=db_derived.id, baseMetric=db_derived.id)
        database.execute(association)
    existing_metriccategory_ids = [assoc.category for assoc in database.execute(
        metriccategory_metric.select().where(metriccategory_metric.c.metrics == db_derived.id))]

    metriccategorys_to_remove = set(existing_metriccategory_ids) - set(derived_data.category)
    for metriccategory_id in metriccategorys_to_remove:
        association = metriccategory_metric.delete().where(
            (metriccategory_metric.c.metrics == db_derived.id) & (metriccategory_metric.c.category == metriccategory_id))
        database.execute(association)

    new_metriccategory_ids = set(derived_data.category) - set(existing_metriccategory_ids)
    for metriccategory_id in new_metriccategory_ids:
        db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
        if db_metriccategory is None:
            raise HTTPException(status_code=404, detail=f"MetricCategory with ID {metriccategory_id} not found")
        association = metriccategory_metric.insert().values(category=db_metriccategory.id, metrics=db_derived.id)
        database.execute(association)
    database.commit()
    database.refresh(db_derived)

    metric_ids = database.query(derived_metric.c.baseMetric).filter(derived_metric.c.derivedBy == db_derived.id).all()
    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == db_derived.id).all()
    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == db_derived.id).all()
    measures_ids = database.query(Measure.id).filter(Measure.metric_id == db_derived.id).all()
    response_data = {
        "derived": db_derived,
        "metric_ids": [x[0] for x in metric_ids],
        "derived_ids": [x[0] for x in derived_ids],
        "metriccategory_ids": [x[0] for x in metriccategory_ids],
        "measures_ids": [x[0] for x in measures_ids]    }
    return response_data


@app.delete("/derived/{derived_id}/", response_model=None, tags=["Derived"])
async def delete_derived(derived_id: int, database: Session = Depends(get_db)):
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")
    database.delete(db_derived)
    database.commit()
    return db_derived

@app.post("/derived/{derived_id}/baseMetric/{metric_id}/", response_model=None, tags=["Derived Relationships"])
async def add_baseMetric_to_derived(derived_id: int, metric_id: int, database: Session = Depends(get_db)):
    """Add a Metric to this Derived's baseMetric relationship"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    db_metric = database.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    # Check if relationship already exists
    existing = database.query(derived_metric).filter(
        (derived_metric.c.derivedBy == derived_id) &
        (derived_metric.c.baseMetric == metric_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = derived_metric.insert().values(derivedBy=derived_id, baseMetric=metric_id)
    database.execute(association)
    database.commit()

    return {"message": "Metric added to baseMetric successfully"}


@app.delete("/derived/{derived_id}/baseMetric/{metric_id}/", response_model=None, tags=["Derived Relationships"])
async def remove_baseMetric_from_derived(derived_id: int, metric_id: int, database: Session = Depends(get_db)):
    """Remove a Metric from this Derived's baseMetric relationship"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    # Check if relationship exists
    existing = database.query(derived_metric).filter(
        (derived_metric.c.derivedBy == derived_id) &
        (derived_metric.c.baseMetric == metric_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = derived_metric.delete().where(
        (derived_metric.c.derivedBy == derived_id) &
        (derived_metric.c.baseMetric == metric_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Metric removed from baseMetric successfully"}


@app.get("/derived/{derived_id}/baseMetric/", response_model=None, tags=["Derived Relationships"])
async def get_baseMetric_of_derived(derived_id: int, database: Session = Depends(get_db)):
    """Get all Metric entities related to this Derived through baseMetric"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    metric_ids = database.query(derived_metric.c.baseMetric).filter(derived_metric.c.derivedBy == derived_id).all()
    metric_list = database.query(Metric).filter(Metric.id.in_([id[0] for id in metric_ids])).all()

    return {
        "derived_id": derived_id,
        "baseMetric_count": len(metric_list),
        "baseMetric": metric_list
    }

@app.post("/derived/{derived_id}/derivedBy/{related_derived_id}/", response_model=None, tags=["Derived Relationships"])
async def add_derivedBy_to_derived(derived_id: int, related_derived_id: int, database: Session = Depends(get_db)):
    """Add a Derived to this Derived's derivedBy relationship"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    db_derived = database.query(Derived).filter(Derived.id == related_derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    # Check if relationship already exists
    existing = database.query(derived_metric).filter(
        (derived_metric.c.baseMetric == derived_id) &
        (derived_metric.c.derivedBy == related_derived_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = derived_metric.insert().values(baseMetric=derived_id, derivedBy=related_derived_id)
    database.execute(association)
    database.commit()

    return {"message": "Derived added to derivedBy successfully"}


@app.delete("/derived/{derived_id}/derivedBy/{related_derived_id}/", response_model=None, tags=["Derived Relationships"])
async def remove_derivedBy_from_derived(derived_id: int, related_derived_id: int, database: Session = Depends(get_db)):
    """Remove a Derived from this Derived's derivedBy relationship"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    # Check if relationship exists
    existing = database.query(derived_metric).filter(
        (derived_metric.c.baseMetric == derived_id) &
        (derived_metric.c.derivedBy == related_derived_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = derived_metric.delete().where(
        (derived_metric.c.baseMetric == derived_id) &
        (derived_metric.c.derivedBy == related_derived_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Derived removed from derivedBy successfully"}


@app.get("/derived/{derived_id}/derivedBy/", response_model=None, tags=["Derived Relationships"])
async def get_derivedBy_of_derived(derived_id: int, database: Session = Depends(get_db)):
    """Get all Derived entities related to this Derived through derivedBy"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == derived_id).all()
    derived_list = database.query(Derived).filter(Derived.id.in_([id[0] for id in derived_ids])).all()

    return {
        "derived_id": derived_id,
        "derivedBy_count": len(derived_list),
        "derivedBy": derived_list
    }

@app.post("/derived/{derived_id}/category/{metriccategory_id}/", response_model=None, tags=["Derived Relationships"])
async def add_category_to_derived(derived_id: int, metriccategory_id: int, database: Session = Depends(get_db)):
    """Add a MetricCategory to this Derived's category relationship"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
    if db_metriccategory is None:
        raise HTTPException(status_code=404, detail="MetricCategory not found")

    # Check if relationship already exists
    existing = database.query(metriccategory_metric).filter(
        (metriccategory_metric.c.metrics == derived_id) &
        (metriccategory_metric.c.category == metriccategory_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = metriccategory_metric.insert().values(metrics=derived_id, category=metriccategory_id)
    database.execute(association)
    database.commit()

    return {"message": "MetricCategory added to category successfully"}


@app.delete("/derived/{derived_id}/category/{metriccategory_id}/", response_model=None, tags=["Derived Relationships"])
async def remove_category_from_derived(derived_id: int, metriccategory_id: int, database: Session = Depends(get_db)):
    """Remove a MetricCategory from this Derived's category relationship"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    # Check if relationship exists
    existing = database.query(metriccategory_metric).filter(
        (metriccategory_metric.c.metrics == derived_id) &
        (metriccategory_metric.c.category == metriccategory_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = metriccategory_metric.delete().where(
        (metriccategory_metric.c.metrics == derived_id) &
        (metriccategory_metric.c.category == metriccategory_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "MetricCategory removed from category successfully"}


@app.get("/derived/{derived_id}/category/", response_model=None, tags=["Derived Relationships"])
async def get_category_of_derived(derived_id: int, database: Session = Depends(get_db)):
    """Get all MetricCategory entities related to this Derived through category"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == derived_id).all()
    metriccategory_list = database.query(MetricCategory).filter(MetricCategory.id.in_([id[0] for id in metriccategory_ids])).all()

    return {
        "derived_id": derived_id,
        "category_count": len(metriccategory_list),
        "category": metriccategory_list
    }


@app.get("/derived/{derived_id}/measures/", response_model=None, tags=["Derived Relationships"])
async def get_measures_of_derived(derived_id: int, database: Session = Depends(get_db)):
    """Get all Measure entities related to this Derived through measures"""
    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    measures_list = database.query(Measure).filter(Measure.metric_id == derived_id).all()

    return {
        "derived_id": derived_id,
        "measures_count": len(measures_list),
        "measures": measures_list
    }





############################################
#
#   Direct functions
#
############################################

@app.get("/direct/", response_model=None, tags=["Direct"])
def get_all_direct(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Direct)
        direct_list = query.all()

        # Serialize with relationships included
        result = []
        for direct_item in direct_list:
            item_dict = direct_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            derived_list = database.query(Derived).join(derived_metric, Derived.id == derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == direct_item.id).all()
            item_dict['derivedBy'] = []
            for derived_obj in derived_list:
                derived_dict = derived_obj.__dict__.copy()
                derived_dict.pop('_sa_instance_state', None)
                item_dict['derivedBy'].append(derived_dict)
            metriccategory_list = database.query(MetricCategory).join(metriccategory_metric, MetricCategory.id == metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == direct_item.id).all()
            item_dict['category'] = []
            for metriccategory_obj in metriccategory_list:
                metriccategory_dict = metriccategory_obj.__dict__.copy()
                metriccategory_dict.pop('_sa_instance_state', None)
                item_dict['category'].append(metriccategory_dict)
            measure_list = database.query(Measure).filter(Measure.metric_id == direct_item.id).all()
            item_dict['measures'] = []
            for measure_obj in measure_list:
                measure_dict = measure_obj.__dict__.copy()
                measure_dict.pop('_sa_instance_state', None)
                item_dict['measures'].append(measure_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Direct).all()


@app.get("/direct/count/", response_model=None, tags=["Direct"])
def get_count_direct(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Direct entities"""
    count = database.query(Direct).count()
    return {"count": count}


@app.get("/direct/paginated/", response_model=None, tags=["Direct"])
def get_paginated_direct(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Direct entities"""
    total = database.query(Direct).count()
    direct_list = database.query(Direct).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": direct_list
        }

    result = []
    for direct_item in direct_list:
        derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == direct_item.id).all()
        metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == direct_item.id).all()
        measures_ids = database.query(Measure.id).filter(Measure.metric_id == direct_item.id).all()
        item_data = {
            "direct": direct_item,
            "derived_ids": [x[0] for x in derived_ids],
            "metriccategory_ids": [x[0] for x in metriccategory_ids],
            "measures_ids": [x[0] for x in measures_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/direct/search/", response_model=None, tags=["Direct"])
def search_direct(
    database: Session = Depends(get_db)
) -> list:
    """Search Direct entities by attributes"""
    query = database.query(Direct)


    results = query.all()
    return results


@app.get("/direct/{direct_id}/", response_model=None, tags=["Direct"])
async def get_direct(direct_id: int, database: Session = Depends(get_db)) -> Direct:
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")

    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == db_direct.id).all()
    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == db_direct.id).all()
    measures_ids = database.query(Measure.id).filter(Measure.metric_id == db_direct.id).all()
    response_data = {
        "direct": db_direct,
        "derived_ids": [x[0] for x in derived_ids],
        "metriccategory_ids": [x[0] for x in metriccategory_ids],
        "measures_ids": [x[0] for x in measures_ids]}
    return response_data



@app.post("/direct/", response_model=None, tags=["Direct"])
async def create_direct(direct_data: DirectCreate, database: Session = Depends(get_db)) -> Direct:

    if direct_data.derivedBy:
        for id in direct_data.derivedBy:
            # Entity already validated before creation
            db_derived = database.query(Derived).filter(Derived.id == id).first()
            if not db_derived:
                raise HTTPException(status_code=404, detail=f"Derived with ID {id} not found")
    if direct_data.category:
        for id in direct_data.category:
            # Entity already validated before creation
            db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == id).first()
            if not db_metriccategory:
                raise HTTPException(status_code=404, detail=f"MetricCategory with ID {id} not found")

    db_direct = Direct(
        name=direct_data.name,        description=direct_data.description        )

    database.add(db_direct)
    database.commit()
    database.refresh(db_direct)

    if direct_data.measures:
        # Validate that all Measure IDs exist
        for measure_id in direct_data.measures:
            db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
            if not db_measure:
                raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

        # Update the related entities with the new foreign key
        database.query(Measure).filter(Measure.id.in_(direct_data.measures)).update(
            {Measure.metric_id: db_direct.id}, synchronize_session=False
        )
        database.commit()

    if direct_data.derivedBy:
        for id in direct_data.derivedBy:
            # Entity already validated before creation
            db_derived = database.query(Derived).filter(Derived.id == id).first()
            # Create the association
            association = derived_metric.insert().values(baseMetric=db_direct.id, derivedBy=db_derived.id)
            database.execute(association)
            database.commit()
    if direct_data.category:
        for id in direct_data.category:
            # Entity already validated before creation
            db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == id).first()
            # Create the association
            association = metriccategory_metric.insert().values(metrics=db_direct.id, category=db_metriccategory.id)
            database.execute(association)
            database.commit()


    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == db_direct.id).all()
    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == db_direct.id).all()
    measures_ids = database.query(Measure.id).filter(Measure.metric_id == db_direct.id).all()
    response_data = {
        "direct": db_direct,
        "derived_ids": [x[0] for x in derived_ids],
        "metriccategory_ids": [x[0] for x in metriccategory_ids],
        "measures_ids": [x[0] for x in measures_ids]    }
    return response_data


@app.post("/direct/bulk/", response_model=None, tags=["Direct"])
async def bulk_create_direct(items: list[DirectCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Direct entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_direct = Direct(
                name=item_data.name,                description=item_data.description            )
            database.add(db_direct)
            database.flush()  # Get ID without committing
            created_items.append(db_direct.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Direct entities"
    }


@app.delete("/direct/bulk/", response_model=None, tags=["Direct"])
async def bulk_delete_direct(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Direct entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_direct = database.query(Direct).filter(Direct.id == item_id).first()
        if db_direct:
            database.delete(db_direct)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Direct entities"
    }

@app.put("/direct/{direct_id}/", response_model=None, tags=["Direct"])
async def update_direct(direct_id: int, direct_data: DirectCreate, database: Session = Depends(get_db)) -> Direct:
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")

    if direct_data.measures is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Measure).filter(Measure.metric_id == db_direct.id).update(
            {Measure.metric_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if direct_data.measures:
            # Validate that all IDs exist
            for measure_id in direct_data.measures:
                db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
                if not db_measure:
                    raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

            # Update the related entities with the new foreign key
            database.query(Measure).filter(Measure.id.in_(direct_data.measures)).update(
                {Measure.metric_id: db_direct.id}, synchronize_session=False
            )
    existing_derived_ids = [assoc.derivedBy for assoc in database.execute(
        derived_metric.select().where(derived_metric.c.baseMetric == db_direct.id))]

    deriveds_to_remove = set(existing_derived_ids) - set(direct_data.derivedBy)
    for derived_id in deriveds_to_remove:
        association = derived_metric.delete().where(
            (derived_metric.c.baseMetric == db_direct.id) & (derived_metric.c.derivedBy == derived_id))
        database.execute(association)

    new_derived_ids = set(direct_data.derivedBy) - set(existing_derived_ids)
    for derived_id in new_derived_ids:
        db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
        if db_derived is None:
            raise HTTPException(status_code=404, detail=f"Derived with ID {derived_id} not found")
        association = derived_metric.insert().values(derivedBy=db_derived.id, baseMetric=db_direct.id)
        database.execute(association)
    existing_metriccategory_ids = [assoc.category for assoc in database.execute(
        metriccategory_metric.select().where(metriccategory_metric.c.metrics == db_direct.id))]

    metriccategorys_to_remove = set(existing_metriccategory_ids) - set(direct_data.category)
    for metriccategory_id in metriccategorys_to_remove:
        association = metriccategory_metric.delete().where(
            (metriccategory_metric.c.metrics == db_direct.id) & (metriccategory_metric.c.category == metriccategory_id))
        database.execute(association)

    new_metriccategory_ids = set(direct_data.category) - set(existing_metriccategory_ids)
    for metriccategory_id in new_metriccategory_ids:
        db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
        if db_metriccategory is None:
            raise HTTPException(status_code=404, detail=f"MetricCategory with ID {metriccategory_id} not found")
        association = metriccategory_metric.insert().values(category=db_metriccategory.id, metrics=db_direct.id)
        database.execute(association)
    database.commit()
    database.refresh(db_direct)

    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == db_direct.id).all()
    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == db_direct.id).all()
    measures_ids = database.query(Measure.id).filter(Measure.metric_id == db_direct.id).all()
    response_data = {
        "direct": db_direct,
        "derived_ids": [x[0] for x in derived_ids],
        "metriccategory_ids": [x[0] for x in metriccategory_ids],
        "measures_ids": [x[0] for x in measures_ids]    }
    return response_data


@app.delete("/direct/{direct_id}/", response_model=None, tags=["Direct"])
async def delete_direct(direct_id: int, database: Session = Depends(get_db)):
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")
    database.delete(db_direct)
    database.commit()
    return db_direct

@app.post("/direct/{direct_id}/derivedBy/{derived_id}/", response_model=None, tags=["Direct Relationships"])
async def add_derivedBy_to_direct(direct_id: int, derived_id: int, database: Session = Depends(get_db)):
    """Add a Derived to this Direct's derivedBy relationship"""
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")

    db_derived = database.query(Derived).filter(Derived.id == derived_id).first()
    if db_derived is None:
        raise HTTPException(status_code=404, detail="Derived not found")

    # Check if relationship already exists
    existing = database.query(derived_metric).filter(
        (derived_metric.c.baseMetric == direct_id) &
        (derived_metric.c.derivedBy == derived_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = derived_metric.insert().values(baseMetric=direct_id, derivedBy=derived_id)
    database.execute(association)
    database.commit()

    return {"message": "Derived added to derivedBy successfully"}


@app.delete("/direct/{direct_id}/derivedBy/{derived_id}/", response_model=None, tags=["Direct Relationships"])
async def remove_derivedBy_from_direct(direct_id: int, derived_id: int, database: Session = Depends(get_db)):
    """Remove a Derived from this Direct's derivedBy relationship"""
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")

    # Check if relationship exists
    existing = database.query(derived_metric).filter(
        (derived_metric.c.baseMetric == direct_id) &
        (derived_metric.c.derivedBy == derived_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = derived_metric.delete().where(
        (derived_metric.c.baseMetric == direct_id) &
        (derived_metric.c.derivedBy == derived_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Derived removed from derivedBy successfully"}


@app.get("/direct/{direct_id}/derivedBy/", response_model=None, tags=["Direct Relationships"])
async def get_derivedBy_of_direct(direct_id: int, database: Session = Depends(get_db)):
    """Get all Derived entities related to this Direct through derivedBy"""
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")

    derived_ids = database.query(derived_metric.c.derivedBy).filter(derived_metric.c.baseMetric == direct_id).all()
    derived_list = database.query(Derived).filter(Derived.id.in_([id[0] for id in derived_ids])).all()

    return {
        "direct_id": direct_id,
        "derivedBy_count": len(derived_list),
        "derivedBy": derived_list
    }

@app.post("/direct/{direct_id}/category/{metriccategory_id}/", response_model=None, tags=["Direct Relationships"])
async def add_category_to_direct(direct_id: int, metriccategory_id: int, database: Session = Depends(get_db)):
    """Add a MetricCategory to this Direct's category relationship"""
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")

    db_metriccategory = database.query(MetricCategory).filter(MetricCategory.id == metriccategory_id).first()
    if db_metriccategory is None:
        raise HTTPException(status_code=404, detail="MetricCategory not found")

    # Check if relationship already exists
    existing = database.query(metriccategory_metric).filter(
        (metriccategory_metric.c.metrics == direct_id) &
        (metriccategory_metric.c.category == metriccategory_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = metriccategory_metric.insert().values(metrics=direct_id, category=metriccategory_id)
    database.execute(association)
    database.commit()

    return {"message": "MetricCategory added to category successfully"}


@app.delete("/direct/{direct_id}/category/{metriccategory_id}/", response_model=None, tags=["Direct Relationships"])
async def remove_category_from_direct(direct_id: int, metriccategory_id: int, database: Session = Depends(get_db)):
    """Remove a MetricCategory from this Direct's category relationship"""
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")

    # Check if relationship exists
    existing = database.query(metriccategory_metric).filter(
        (metriccategory_metric.c.metrics == direct_id) &
        (metriccategory_metric.c.category == metriccategory_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = metriccategory_metric.delete().where(
        (metriccategory_metric.c.metrics == direct_id) &
        (metriccategory_metric.c.category == metriccategory_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "MetricCategory removed from category successfully"}


@app.get("/direct/{direct_id}/category/", response_model=None, tags=["Direct Relationships"])
async def get_category_of_direct(direct_id: int, database: Session = Depends(get_db)):
    """Get all MetricCategory entities related to this Direct through category"""
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")

    metriccategory_ids = database.query(metriccategory_metric.c.category).filter(metriccategory_metric.c.metrics == direct_id).all()
    metriccategory_list = database.query(MetricCategory).filter(MetricCategory.id.in_([id[0] for id in metriccategory_ids])).all()

    return {
        "direct_id": direct_id,
        "category_count": len(metriccategory_list),
        "category": metriccategory_list
    }


@app.get("/direct/{direct_id}/measures/", response_model=None, tags=["Direct Relationships"])
async def get_measures_of_direct(direct_id: int, database: Session = Depends(get_db)):
    """Get all Measure entities related to this Direct through measures"""
    db_direct = database.query(Direct).filter(Direct.id == direct_id).first()
    if db_direct is None:
        raise HTTPException(status_code=404, detail="Direct not found")

    measures_list = database.query(Measure).filter(Measure.metric_id == direct_id).all()

    return {
        "direct_id": direct_id,
        "measures_count": len(measures_list),
        "measures": measures_list
    }





############################################
#
#   Evaluation functions
#
############################################

@app.get("/evaluation/", response_model=None, tags=["Evaluation"])
def get_all_evaluation(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Evaluation)
        query = query.options(joinedload(Evaluation.project))
        query = query.options(joinedload(Evaluation.evaluates))
        query = query.options(joinedload(Evaluation.config))
        evaluation_list = query.all()

        # Serialize with relationships included
        result = []
        for evaluation_item in evaluation_list:
            item_dict = evaluation_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if evaluation_item.project:
                related_obj = evaluation_item.project
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['project'] = related_dict
            else:
                item_dict['project'] = None
            if evaluation_item.evaluates:
                related_obj = evaluation_item.evaluates
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['evaluates'] = related_dict
            else:
                item_dict['evaluates'] = None
            if evaluation_item.config:
                related_obj = evaluation_item.config
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['config'] = related_dict
            else:
                item_dict['config'] = None

            # Add many-to-many and one-to-many relationship objects (full details)
            element_list = database.query(Element).join(evaluation_element, Element.id == evaluation_element.c.ref).filter(evaluation_element.c.eval == evaluation_item.id).all()
            item_dict['ref'] = []
            for element_obj in element_list:
                element_dict = element_obj.__dict__.copy()
                element_dict.pop('_sa_instance_state', None)
                item_dict['ref'].append(element_dict)
            observation_list = database.query(Observation).filter(Observation.eval_id == evaluation_item.id).all()
            item_dict['observations'] = []
            for observation_obj in observation_list:
                observation_dict = observation_obj.__dict__.copy()
                observation_dict.pop('_sa_instance_state', None)
                item_dict['observations'].append(observation_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Evaluation).all()


@app.get("/evaluation/count/", response_model=None, tags=["Evaluation"])
def get_count_evaluation(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Evaluation entities"""
    count = database.query(Evaluation).count()
    return {"count": count}


@app.get("/evaluation/paginated/", response_model=None, tags=["Evaluation"])
def get_paginated_evaluation(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Evaluation entities"""
    total = database.query(Evaluation).count()
    evaluation_list = database.query(Evaluation).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": evaluation_list
        }

    result = []
    for evaluation_item in evaluation_list:
        element_ids = database.query(evaluation_element.c.ref).filter(evaluation_element.c.eval == evaluation_item.id).all()
        observations_ids = database.query(Observation.id).filter(Observation.eval_id == evaluation_item.id).all()
        item_data = {
            "evaluation": evaluation_item,
            "element_ids": [x[0] for x in element_ids],
            "observations_ids": [x[0] for x in observations_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/evaluation/search/", response_model=None, tags=["Evaluation"])
def search_evaluation(
    database: Session = Depends(get_db)
) -> list:
    """Search Evaluation entities by attributes"""
    query = database.query(Evaluation)


    results = query.all()
    return results


@app.get("/evaluation/{evaluation_id}/", response_model=None, tags=["Evaluation"])
async def get_evaluation(evaluation_id: int, database: Session = Depends(get_db)) -> Evaluation:
    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    element_ids = database.query(evaluation_element.c.ref).filter(evaluation_element.c.eval == db_evaluation.id).all()
    observations_ids = database.query(Observation.id).filter(Observation.eval_id == db_evaluation.id).all()
    response_data = {
        "evaluation": db_evaluation,
        "element_ids": [x[0] for x in element_ids],
        "observations_ids": [x[0] for x in observations_ids]}
    return response_data



@app.post("/evaluation/", response_model=None, tags=["Evaluation"])
async def create_evaluation(evaluation_data: EvaluationCreate, database: Session = Depends(get_db)) -> Evaluation:

    if evaluation_data.project is not None:
        db_project = database.query(Project).filter(Project.id == evaluation_data.project).first()
        if not db_project:
            raise HTTPException(status_code=400, detail="Project not found")
    else:
        raise HTTPException(status_code=400, detail="Project ID is required")
    if evaluation_data.evaluates is not None:
        db_evaluates = database.query(Element).filter(Element.id == evaluation_data.evaluates).first()
        if not db_evaluates:
            raise HTTPException(status_code=400, detail="Element not found")
    else:
        raise HTTPException(status_code=400, detail="Element ID is required")
    if evaluation_data.config is not None:
        db_config = database.query(Configuration).filter(Configuration.id == evaluation_data.config).first()
        if not db_config:
            raise HTTPException(status_code=400, detail="Configuration not found")
    else:
        raise HTTPException(status_code=400, detail="Configuration ID is required")
    if evaluation_data.ref:
        for id in evaluation_data.ref:
            # Entity already validated before creation
            db_element = database.query(Element).filter(Element.id == id).first()
            if not db_element:
                raise HTTPException(status_code=404, detail=f"Element with ID {id} not found")

    db_evaluation = Evaluation(
        status=evaluation_data.status.value,        project_id=evaluation_data.project,        evaluates_id=evaluation_data.evaluates,        config_id=evaluation_data.config        )

    database.add(db_evaluation)
    database.commit()
    database.refresh(db_evaluation)

    if evaluation_data.observations:
        # Validate that all Observation IDs exist
        for observation_id in evaluation_data.observations:
            db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
            if not db_observation:
                raise HTTPException(status_code=400, detail=f"Observation with id {observation_id} not found")

        # Update the related entities with the new foreign key
        database.query(Observation).filter(Observation.id.in_(evaluation_data.observations)).update(
            {Observation.eval_id: db_evaluation.id}, synchronize_session=False
        )
        database.commit()

    if evaluation_data.ref:
        for id in evaluation_data.ref:
            # Entity already validated before creation
            db_element = database.query(Element).filter(Element.id == id).first()
            # Create the association
            association = evaluation_element.insert().values(eval=db_evaluation.id, ref=db_element.id)
            database.execute(association)
            database.commit()


    element_ids = database.query(evaluation_element.c.ref).filter(evaluation_element.c.eval == db_evaluation.id).all()
    observations_ids = database.query(Observation.id).filter(Observation.eval_id == db_evaluation.id).all()
    response_data = {
        "evaluation": db_evaluation,
        "element_ids": [x[0] for x in element_ids],
        "observations_ids": [x[0] for x in observations_ids]    }
    return response_data


@app.post("/evaluation/bulk/", response_model=None, tags=["Evaluation"])
async def bulk_create_evaluation(items: list[EvaluationCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Evaluation entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.project:
                raise ValueError("Project ID is required")
            if not item_data.evaluates:
                raise ValueError("Element ID is required")
            if not item_data.config:
                raise ValueError("Configuration ID is required")

            db_evaluation = Evaluation(
                status=item_data.status.value,                project_id=item_data.project,                evaluates_id=item_data.evaluates,                config_id=item_data.config            )
            database.add(db_evaluation)
            database.flush()  # Get ID without committing
            created_items.append(db_evaluation.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Evaluation entities"
    }


@app.delete("/evaluation/bulk/", response_model=None, tags=["Evaluation"])
async def bulk_delete_evaluation(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Evaluation entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_evaluation = database.query(Evaluation).filter(Evaluation.id == item_id).first()
        if db_evaluation:
            database.delete(db_evaluation)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Evaluation entities"
    }

@app.put("/evaluation/{evaluation_id}/", response_model=None, tags=["Evaluation"])
async def update_evaluation(evaluation_id: int, evaluation_data: EvaluationCreate, database: Session = Depends(get_db)) -> Evaluation:
    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    setattr(db_evaluation, 'status', evaluation_data.status.value)
    if evaluation_data.project is not None:
        db_project = database.query(Project).filter(Project.id == evaluation_data.project).first()
        if not db_project:
            raise HTTPException(status_code=400, detail="Project not found")
        setattr(db_evaluation, 'project_id', evaluation_data.project)
    if evaluation_data.evaluates is not None:
        db_evaluates = database.query(Element).filter(Element.id == evaluation_data.evaluates).first()
        if not db_evaluates:
            raise HTTPException(status_code=400, detail="Element not found")
        setattr(db_evaluation, 'evaluates_id', evaluation_data.evaluates)
    if evaluation_data.config is not None:
        db_config = database.query(Configuration).filter(Configuration.id == evaluation_data.config).first()
        if not db_config:
            raise HTTPException(status_code=400, detail="Configuration not found")
        setattr(db_evaluation, 'config_id', evaluation_data.config)
    if evaluation_data.observations is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Observation).filter(Observation.eval_id == db_evaluation.id).update(
            {Observation.eval_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if evaluation_data.observations:
            # Validate that all IDs exist
            for observation_id in evaluation_data.observations:
                db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
                if not db_observation:
                    raise HTTPException(status_code=400, detail=f"Observation with id {observation_id} not found")

            # Update the related entities with the new foreign key
            database.query(Observation).filter(Observation.id.in_(evaluation_data.observations)).update(
                {Observation.eval_id: db_evaluation.id}, synchronize_session=False
            )
    existing_element_ids = [assoc.ref for assoc in database.execute(
        evaluation_element.select().where(evaluation_element.c.eval == db_evaluation.id))]

    elements_to_remove = set(existing_element_ids) - set(evaluation_data.ref)
    for element_id in elements_to_remove:
        association = evaluation_element.delete().where(
            (evaluation_element.c.eval == db_evaluation.id) & (evaluation_element.c.ref == element_id))
        database.execute(association)

    new_element_ids = set(evaluation_data.ref) - set(existing_element_ids)
    for element_id in new_element_ids:
        db_element = database.query(Element).filter(Element.id == element_id).first()
        if db_element is None:
            raise HTTPException(status_code=404, detail=f"Element with ID {element_id} not found")
        association = evaluation_element.insert().values(ref=db_element.id, eval=db_evaluation.id)
        database.execute(association)
    database.commit()
    database.refresh(db_evaluation)

    element_ids = database.query(evaluation_element.c.ref).filter(evaluation_element.c.eval == db_evaluation.id).all()
    observations_ids = database.query(Observation.id).filter(Observation.eval_id == db_evaluation.id).all()
    response_data = {
        "evaluation": db_evaluation,
        "element_ids": [x[0] for x in element_ids],
        "observations_ids": [x[0] for x in observations_ids]    }
    return response_data


@app.delete("/evaluation/{evaluation_id}/", response_model=None, tags=["Evaluation"])
async def delete_evaluation(evaluation_id: int, database: Session = Depends(get_db)):
    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    database.delete(db_evaluation)
    database.commit()
    return db_evaluation

@app.post("/evaluation/{evaluation_id}/ref/{element_id}/", response_model=None, tags=["Evaluation Relationships"])
async def add_ref_to_evaluation(evaluation_id: int, element_id: int, database: Session = Depends(get_db)):
    """Add a Element to this Evaluation's ref relationship"""
    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    db_element = database.query(Element).filter(Element.id == element_id).first()
    if db_element is None:
        raise HTTPException(status_code=404, detail="Element not found")

    # Check if relationship already exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.eval == evaluation_id) &
        (evaluation_element.c.ref == element_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = evaluation_element.insert().values(eval=evaluation_id, ref=element_id)
    database.execute(association)
    database.commit()

    return {"message": "Element added to ref successfully"}


@app.delete("/evaluation/{evaluation_id}/ref/{element_id}/", response_model=None, tags=["Evaluation Relationships"])
async def remove_ref_from_evaluation(evaluation_id: int, element_id: int, database: Session = Depends(get_db)):
    """Remove a Element from this Evaluation's ref relationship"""
    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Check if relationship exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.eval == evaluation_id) &
        (evaluation_element.c.ref == element_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = evaluation_element.delete().where(
        (evaluation_element.c.eval == evaluation_id) &
        (evaluation_element.c.ref == element_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Element removed from ref successfully"}


@app.get("/evaluation/{evaluation_id}/ref/", response_model=None, tags=["Evaluation Relationships"])
async def get_ref_of_evaluation(evaluation_id: int, database: Session = Depends(get_db)):
    """Get all Element entities related to this Evaluation through ref"""
    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    element_ids = database.query(evaluation_element.c.ref).filter(evaluation_element.c.eval == evaluation_id).all()
    element_list = database.query(Element).filter(Element.id.in_([id[0] for id in element_ids])).all()

    return {
        "evaluation_id": evaluation_id,
        "ref_count": len(element_list),
        "ref": element_list
    }


@app.get("/evaluation/{evaluation_id}/observations/", response_model=None, tags=["Evaluation Relationships"])
async def get_observations_of_evaluation(evaluation_id: int, database: Session = Depends(get_db)):
    """Get all Observation entities related to this Evaluation through observations"""
    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    observations_list = database.query(Observation).filter(Observation.eval_id == evaluation_id).all()

    return {
        "evaluation_id": evaluation_id,
        "observations_count": len(observations_list),
        "observations": observations_list
    }





############################################
#
#   Observation functions
#
############################################

@app.get("/observation/", response_model=None, tags=["Observation"])
def get_all_observation(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Observation)
        query = query.options(joinedload(Observation.eval))
        query = query.options(joinedload(Observation.tool))
        query = query.options(joinedload(Observation.dataset))
        observation_list = query.all()

        # Serialize with relationships included
        result = []
        for observation_item in observation_list:
            item_dict = observation_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if observation_item.eval:
                related_obj = observation_item.eval
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['eval'] = related_dict
            else:
                item_dict['eval'] = None
            if observation_item.tool:
                related_obj = observation_item.tool
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['tool'] = related_dict
            else:
                item_dict['tool'] = None
            if observation_item.dataset:
                related_obj = observation_item.dataset
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['dataset'] = related_dict
            else:
                item_dict['dataset'] = None

            # Add many-to-many and one-to-many relationship objects (full details)
            measure_list = database.query(Measure).filter(Measure.observation_id == observation_item.id).all()
            item_dict['measures'] = []
            for measure_obj in measure_list:
                measure_dict = measure_obj.__dict__.copy()
                measure_dict.pop('_sa_instance_state', None)
                item_dict['measures'].append(measure_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Observation).all()


@app.get("/observation/count/", response_model=None, tags=["Observation"])
def get_count_observation(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Observation entities"""
    count = database.query(Observation).count()
    return {"count": count}


@app.get("/observation/paginated/", response_model=None, tags=["Observation"])
def get_paginated_observation(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Observation entities"""
    total = database.query(Observation).count()
    observation_list = database.query(Observation).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": observation_list
        }

    result = []
    for observation_item in observation_list:
        measures_ids = database.query(Measure.id).filter(Measure.observation_id == observation_item.id).all()
        item_data = {
            "observation": observation_item,
            "measures_ids": [x[0] for x in measures_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/observation/search/", response_model=None, tags=["Observation"])
def search_observation(
    database: Session = Depends(get_db)
) -> list:
    """Search Observation entities by attributes"""
    query = database.query(Observation)


    results = query.all()
    return results


@app.get("/observation/{observation_id}/", response_model=None, tags=["Observation"])
async def get_observation(observation_id: int, database: Session = Depends(get_db)) -> Observation:
    db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
    if db_observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")

    measures_ids = database.query(Measure.id).filter(Measure.observation_id == db_observation.id).all()
    response_data = {
        "observation": db_observation,
        "measures_ids": [x[0] for x in measures_ids]}
    return response_data



@app.post("/observation/", response_model=None, tags=["Observation"])
async def create_observation(observation_data: ObservationCreate, database: Session = Depends(get_db)) -> Observation:

    if observation_data.eval is not None:
        db_eval = database.query(Evaluation).filter(Evaluation.id == observation_data.eval).first()
        if not db_eval:
            raise HTTPException(status_code=400, detail="Evaluation not found")
    else:
        raise HTTPException(status_code=400, detail="Evaluation ID is required")
    if observation_data.tool is not None:
        db_tool = database.query(Tool).filter(Tool.id == observation_data.tool).first()
        if not db_tool:
            raise HTTPException(status_code=400, detail="Tool not found")
    else:
        raise HTTPException(status_code=400, detail="Tool ID is required")
    if observation_data.dataset is not None:
        db_dataset = database.query(Dataset).filter(Dataset.id == observation_data.dataset).first()
        if not db_dataset:
            raise HTTPException(status_code=400, detail="Dataset not found")
    else:
        raise HTTPException(status_code=400, detail="Dataset ID is required")

    db_observation = Observation(
        name=observation_data.name,        description=observation_data.description,        observer=observation_data.observer,        whenObserved=observation_data.whenObserved,        eval_id=observation_data.eval,        tool_id=observation_data.tool,        dataset_id=observation_data.dataset        )

    database.add(db_observation)
    database.commit()
    database.refresh(db_observation)

    if observation_data.measures:
        # Validate that all Measure IDs exist
        for measure_id in observation_data.measures:
            db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
            if not db_measure:
                raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

        # Update the related entities with the new foreign key
        database.query(Measure).filter(Measure.id.in_(observation_data.measures)).update(
            {Measure.observation_id: db_observation.id}, synchronize_session=False
        )
        database.commit()



    measures_ids = database.query(Measure.id).filter(Measure.observation_id == db_observation.id).all()
    response_data = {
        "observation": db_observation,
        "measures_ids": [x[0] for x in measures_ids]    }
    return response_data


@app.post("/observation/bulk/", response_model=None, tags=["Observation"])
async def bulk_create_observation(items: list[ObservationCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Observation entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.eval:
                raise ValueError("Evaluation ID is required")
            if not item_data.tool:
                raise ValueError("Tool ID is required")
            if not item_data.dataset:
                raise ValueError("Dataset ID is required")

            db_observation = Observation(
                name=item_data.name,                description=item_data.description,                observer=item_data.observer,                whenObserved=item_data.whenObserved,                eval_id=item_data.eval,                tool_id=item_data.tool,                dataset_id=item_data.dataset            )
            database.add(db_observation)
            database.flush()  # Get ID without committing
            created_items.append(db_observation.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Observation entities"
    }


@app.delete("/observation/bulk/", response_model=None, tags=["Observation"])
async def bulk_delete_observation(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Observation entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_observation = database.query(Observation).filter(Observation.id == item_id).first()
        if db_observation:
            database.delete(db_observation)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Observation entities"
    }

@app.put("/observation/{observation_id}/", response_model=None, tags=["Observation"])
async def update_observation(observation_id: int, observation_data: ObservationCreate, database: Session = Depends(get_db)) -> Observation:
    db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
    if db_observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")

    setattr(db_observation, 'observer', observation_data.observer)
    setattr(db_observation, 'whenObserved', observation_data.whenObserved)
    if observation_data.eval is not None:
        db_eval = database.query(Evaluation).filter(Evaluation.id == observation_data.eval).first()
        if not db_eval:
            raise HTTPException(status_code=400, detail="Evaluation not found")
        setattr(db_observation, 'eval_id', observation_data.eval)
    if observation_data.tool is not None:
        db_tool = database.query(Tool).filter(Tool.id == observation_data.tool).first()
        if not db_tool:
            raise HTTPException(status_code=400, detail="Tool not found")
        setattr(db_observation, 'tool_id', observation_data.tool)
    if observation_data.dataset is not None:
        db_dataset = database.query(Dataset).filter(Dataset.id == observation_data.dataset).first()
        if not db_dataset:
            raise HTTPException(status_code=400, detail="Dataset not found")
        setattr(db_observation, 'dataset_id', observation_data.dataset)
    if observation_data.measures is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Measure).filter(Measure.observation_id == db_observation.id).update(
            {Measure.observation_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if observation_data.measures:
            # Validate that all IDs exist
            for measure_id in observation_data.measures:
                db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
                if not db_measure:
                    raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

            # Update the related entities with the new foreign key
            database.query(Measure).filter(Measure.id.in_(observation_data.measures)).update(
                {Measure.observation_id: db_observation.id}, synchronize_session=False
            )
    database.commit()
    database.refresh(db_observation)

    measures_ids = database.query(Measure.id).filter(Measure.observation_id == db_observation.id).all()
    response_data = {
        "observation": db_observation,
        "measures_ids": [x[0] for x in measures_ids]    }
    return response_data


@app.delete("/observation/{observation_id}/", response_model=None, tags=["Observation"])
async def delete_observation(observation_id: int, database: Session = Depends(get_db)):
    db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
    if db_observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")
    database.delete(db_observation)
    database.commit()
    return db_observation


@app.get("/observation/{observation_id}/measures/", response_model=None, tags=["Observation Relationships"])
async def get_measures_of_observation(observation_id: int, database: Session = Depends(get_db)):
    """Get all Measure entities related to this Observation through measures"""
    db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
    if db_observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")

    measures_list = database.query(Measure).filter(Measure.observation_id == observation_id).all()

    return {
        "observation_id": observation_id,
        "measures_count": len(measures_list),
        "measures": measures_list
    }





############################################
#
#   Measure functions
#
############################################

@app.get("/measure/", response_model=None, tags=["Measure"])
def get_all_measure(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Measure)
        query = query.options(joinedload(Measure.measurand))
        query = query.options(joinedload(Measure.observation))
        query = query.options(joinedload(Measure.metric))
        measure_list = query.all()

        # Serialize with relationships included
        result = []
        for measure_item in measure_list:
            item_dict = measure_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if measure_item.measurand:
                related_obj = measure_item.measurand
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['measurand'] = related_dict
            else:
                item_dict['measurand'] = None
            if measure_item.observation:
                related_obj = measure_item.observation
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['observation'] = related_dict
            else:
                item_dict['observation'] = None
            if measure_item.metric:
                related_obj = measure_item.metric
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['metric'] = related_dict
            else:
                item_dict['metric'] = None


            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Measure).all()


@app.get("/measure/count/", response_model=None, tags=["Measure"])
def get_count_measure(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Measure entities"""
    count = database.query(Measure).count()
    return {"count": count}


@app.get("/measure/paginated/", response_model=None, tags=["Measure"])
def get_paginated_measure(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Measure entities"""
    total = database.query(Measure).count()
    measure_list = database.query(Measure).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": measure_list
    }


@app.get("/measure/search/", response_model=None, tags=["Measure"])
def search_measure(
    database: Session = Depends(get_db)
) -> list:
    """Search Measure entities by attributes"""
    query = database.query(Measure)


    results = query.all()
    return results


@app.get("/measure/{measure_id}/", response_model=None, tags=["Measure"])
async def get_measure(measure_id: int, database: Session = Depends(get_db)) -> Measure:
    db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
    if db_measure is None:
        raise HTTPException(status_code=404, detail="Measure not found")

    response_data = {
        "measure": db_measure,
}
    return response_data



@app.post("/measure/", response_model=None, tags=["Measure"])
async def create_measure(measure_data: MeasureCreate, database: Session = Depends(get_db)) -> Measure:

    if measure_data.measurand is not None:
        db_measurand = database.query(Element).filter(Element.id == measure_data.measurand).first()
        if not db_measurand:
            raise HTTPException(status_code=400, detail="Element not found")
    else:
        raise HTTPException(status_code=400, detail="Element ID is required")
    if measure_data.observation is not None:
        db_observation = database.query(Observation).filter(Observation.id == measure_data.observation).first()
        if not db_observation:
            raise HTTPException(status_code=400, detail="Observation not found")
    else:
        raise HTTPException(status_code=400, detail="Observation ID is required")
    if measure_data.metric is not None:
        db_metric = database.query(Metric).filter(Metric.id == measure_data.metric).first()
        if not db_metric:
            raise HTTPException(status_code=400, detail="Metric not found")
    else:
        raise HTTPException(status_code=400, detail="Metric ID is required")

    db_measure = Measure(
        unit=measure_data.unit,        value=measure_data.value,        error=measure_data.error,        uncertainty=measure_data.uncertainty,        measurand_id=measure_data.measurand,        observation_id=measure_data.observation,        metric_id=measure_data.metric        )

    database.add(db_measure)
    database.commit()
    database.refresh(db_measure)




    return db_measure


@app.post("/measure/bulk/", response_model=None, tags=["Measure"])
async def bulk_create_measure(items: list[MeasureCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Measure entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.measurand:
                raise ValueError("Element ID is required")
            if not item_data.observation:
                raise ValueError("Observation ID is required")
            if not item_data.metric:
                raise ValueError("Metric ID is required")

            db_measure = Measure(
                unit=item_data.unit,                value=item_data.value,                error=item_data.error,                uncertainty=item_data.uncertainty,                measurand_id=item_data.measurand,                observation_id=item_data.observation,                metric_id=item_data.metric            )
            database.add(db_measure)
            database.flush()  # Get ID without committing
            created_items.append(db_measure.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Measure entities"
    }


@app.delete("/measure/bulk/", response_model=None, tags=["Measure"])
async def bulk_delete_measure(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Measure entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_measure = database.query(Measure).filter(Measure.id == item_id).first()
        if db_measure:
            database.delete(db_measure)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Measure entities"
    }

@app.put("/measure/{measure_id}/", response_model=None, tags=["Measure"])
async def update_measure(measure_id: int, measure_data: MeasureCreate, database: Session = Depends(get_db)) -> Measure:
    db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
    if db_measure is None:
        raise HTTPException(status_code=404, detail="Measure not found")

    setattr(db_measure, 'unit', measure_data.unit)
    setattr(db_measure, 'value', measure_data.value)
    setattr(db_measure, 'error', measure_data.error)
    setattr(db_measure, 'uncertainty', measure_data.uncertainty)
    if measure_data.measurand is not None:
        db_measurand = database.query(Element).filter(Element.id == measure_data.measurand).first()
        if not db_measurand:
            raise HTTPException(status_code=400, detail="Element not found")
        setattr(db_measure, 'measurand_id', measure_data.measurand)
    if measure_data.observation is not None:
        db_observation = database.query(Observation).filter(Observation.id == measure_data.observation).first()
        if not db_observation:
            raise HTTPException(status_code=400, detail="Observation not found")
        setattr(db_measure, 'observation_id', measure_data.observation)
    if measure_data.metric is not None:
        db_metric = database.query(Metric).filter(Metric.id == measure_data.metric).first()
        if not db_metric:
            raise HTTPException(status_code=400, detail="Metric not found")
        setattr(db_measure, 'metric_id', measure_data.metric)
    database.commit()
    database.refresh(db_measure)

    return db_measure


@app.delete("/measure/{measure_id}/", response_model=None, tags=["Measure"])
async def delete_measure(measure_id: int, database: Session = Depends(get_db)):
    db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
    if db_measure is None:
        raise HTTPException(status_code=404, detail="Measure not found")
    database.delete(db_measure)
    database.commit()
    return db_measure






############################################
#
#   Element functions
#
############################################

@app.get("/element/", response_model=None, tags=["Element"])
def get_all_element(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Element)
        query = query.options(joinedload(Element.project))
        element_list = query.all()

        # Serialize with relationships included
        result = []
        for element_item in element_list:
            item_dict = element_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if element_item.project:
                related_obj = element_item.project
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['project'] = related_dict
            else:
                item_dict['project'] = None

            # Add many-to-many and one-to-many relationship objects (full details)
            evaluation_list = database.query(Evaluation).join(evaluation_element, Evaluation.id == evaluation_element.c.eval).filter(evaluation_element.c.ref == element_item.id).all()
            item_dict['eval'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['eval'].append(evaluation_dict)
            measure_list = database.query(Measure).filter(Measure.measurand_id == element_item.id).all()
            item_dict['measure'] = []
            for measure_obj in measure_list:
                measure_dict = measure_obj.__dict__.copy()
                measure_dict.pop('_sa_instance_state', None)
                item_dict['measure'].append(measure_dict)
            evaluation_list = database.query(Evaluation).filter(Evaluation.evaluates_id == element_item.id).all()
            item_dict['evalu'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['evalu'].append(evaluation_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Element).all()


@app.get("/element/count/", response_model=None, tags=["Element"])
def get_count_element(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Element entities"""
    count = database.query(Element).count()
    return {"count": count}


@app.get("/element/paginated/", response_model=None, tags=["Element"])
def get_paginated_element(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Element entities"""
    total = database.query(Element).count()
    element_list = database.query(Element).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": element_list
        }

    result = []
    for element_item in element_list:
        evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == element_item.id).all()
        measure_ids = database.query(Measure.id).filter(Measure.measurand_id == element_item.id).all()
        evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == element_item.id).all()
        item_data = {
            "element": element_item,
            "evaluation_ids": [x[0] for x in evaluation_ids],
            "measure_ids": [x[0] for x in measure_ids],            "evalu_ids": [x[0] for x in evalu_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/element/search/", response_model=None, tags=["Element"])
def search_element(
    database: Session = Depends(get_db)
) -> list:
    """Search Element entities by attributes"""
    query = database.query(Element)


    results = query.all()
    return results


@app.get("/element/{element_id}/", response_model=None, tags=["Element"])
async def get_element(element_id: int, database: Session = Depends(get_db)) -> Element:
    db_element = database.query(Element).filter(Element.id == element_id).first()
    if db_element is None:
        raise HTTPException(status_code=404, detail="Element not found")

    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_element.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_element.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_element.id).all()
    response_data = {
        "element": db_element,
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]}
    return response_data



@app.post("/element/", response_model=None, tags=["Element"])
async def create_element(element_data: ElementCreate, database: Session = Depends(get_db)) -> Element:

    if element_data.project :
        db_project = database.query(Project).filter(Project.id == element_data.project).first()
        if not db_project:
            raise HTTPException(status_code=400, detail="Project not found")
    if element_data.eval:
        for id in element_data.eval:
            # Entity already validated before creation
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == id).first()
            if not db_evaluation:
                raise HTTPException(status_code=404, detail=f"Evaluation with ID {id} not found")

    db_element = Element(
        name=element_data.name,        description=element_data.description,        project_id=element_data.project        )

    database.add(db_element)
    database.commit()
    database.refresh(db_element)

    if element_data.measure:
        # Validate that all Measure IDs exist
        for measure_id in element_data.measure:
            db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
            if not db_measure:
                raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

        # Update the related entities with the new foreign key
        database.query(Measure).filter(Measure.id.in_(element_data.measure)).update(
            {Measure.measurand_id: db_element.id}, synchronize_session=False
        )
        database.commit()
    if element_data.evalu:
        # Validate that all Evaluation IDs exist
        for evaluation_id in element_data.evalu:
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not db_evaluation:
                raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

        # Update the related entities with the new foreign key
        database.query(Evaluation).filter(Evaluation.id.in_(element_data.evalu)).update(
            {Evaluation.evaluates_id: db_element.id}, synchronize_session=False
        )
        database.commit()

    if element_data.eval:
        for id in element_data.eval:
            # Entity already validated before creation
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == id).first()
            # Create the association
            association = evaluation_element.insert().values(ref=db_element.id, eval=db_evaluation.id)
            database.execute(association)
            database.commit()


    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_element.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_element.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_element.id).all()
    response_data = {
        "element": db_element,
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]    }
    return response_data


@app.post("/element/bulk/", response_model=None, tags=["Element"])
async def bulk_create_element(items: list[ElementCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Element entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_element = Element(
                name=item_data.name,                description=item_data.description,                project_id=item_data.project            )
            database.add(db_element)
            database.flush()  # Get ID without committing
            created_items.append(db_element.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Element entities"
    }


@app.delete("/element/bulk/", response_model=None, tags=["Element"])
async def bulk_delete_element(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Element entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_element = database.query(Element).filter(Element.id == item_id).first()
        if db_element:
            database.delete(db_element)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Element entities"
    }

@app.put("/element/{element_id}/", response_model=None, tags=["Element"])
async def update_element(element_id: int, element_data: ElementCreate, database: Session = Depends(get_db)) -> Element:
    db_element = database.query(Element).filter(Element.id == element_id).first()
    if db_element is None:
        raise HTTPException(status_code=404, detail="Element not found")

    if element_data.project is not None:
        db_project = database.query(Project).filter(Project.id == element_data.project).first()
        if not db_project:
            raise HTTPException(status_code=400, detail="Project not found")
        setattr(db_element, 'project_id', element_data.project)
    else:
        setattr(db_element, 'project_id', None)
    if element_data.measure is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Measure).filter(Measure.measurand_id == db_element.id).update(
            {Measure.measurand_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if element_data.measure:
            # Validate that all IDs exist
            for measure_id in element_data.measure:
                db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
                if not db_measure:
                    raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

            # Update the related entities with the new foreign key
            database.query(Measure).filter(Measure.id.in_(element_data.measure)).update(
                {Measure.measurand_id: db_element.id}, synchronize_session=False
            )
    if element_data.evalu is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Evaluation).filter(Evaluation.evaluates_id == db_element.id).update(
            {Evaluation.evaluates_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if element_data.evalu:
            # Validate that all IDs exist
            for evaluation_id in element_data.evalu:
                db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
                if not db_evaluation:
                    raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

            # Update the related entities with the new foreign key
            database.query(Evaluation).filter(Evaluation.id.in_(element_data.evalu)).update(
                {Evaluation.evaluates_id: db_element.id}, synchronize_session=False
            )
    existing_evaluation_ids = [assoc.eval for assoc in database.execute(
        evaluation_element.select().where(evaluation_element.c.ref == db_element.id))]

    evaluations_to_remove = set(existing_evaluation_ids) - set(element_data.eval)
    for evaluation_id in evaluations_to_remove:
        association = evaluation_element.delete().where(
            (evaluation_element.c.ref == db_element.id) & (evaluation_element.c.eval == evaluation_id))
        database.execute(association)

    new_evaluation_ids = set(element_data.eval) - set(existing_evaluation_ids)
    for evaluation_id in new_evaluation_ids:
        db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if db_evaluation is None:
            raise HTTPException(status_code=404, detail=f"Evaluation with ID {evaluation_id} not found")
        association = evaluation_element.insert().values(eval=db_evaluation.id, ref=db_element.id)
        database.execute(association)
    database.commit()
    database.refresh(db_element)

    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_element.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_element.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_element.id).all()
    response_data = {
        "element": db_element,
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]    }
    return response_data


@app.delete("/element/{element_id}/", response_model=None, tags=["Element"])
async def delete_element(element_id: int, database: Session = Depends(get_db)):
    db_element = database.query(Element).filter(Element.id == element_id).first()
    if db_element is None:
        raise HTTPException(status_code=404, detail="Element not found")
    database.delete(db_element)
    database.commit()
    return db_element

@app.post("/element/{element_id}/eval/{evaluation_id}/", response_model=None, tags=["Element Relationships"])
async def add_eval_to_element(element_id: int, evaluation_id: int, database: Session = Depends(get_db)):
    """Add a Evaluation to this Element's eval relationship"""
    db_element = database.query(Element).filter(Element.id == element_id).first()
    if db_element is None:
        raise HTTPException(status_code=404, detail="Element not found")

    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Check if relationship already exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.ref == element_id) &
        (evaluation_element.c.eval == evaluation_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = evaluation_element.insert().values(ref=element_id, eval=evaluation_id)
    database.execute(association)
    database.commit()

    return {"message": "Evaluation added to eval successfully"}


@app.delete("/element/{element_id}/eval/{evaluation_id}/", response_model=None, tags=["Element Relationships"])
async def remove_eval_from_element(element_id: int, evaluation_id: int, database: Session = Depends(get_db)):
    """Remove a Evaluation from this Element's eval relationship"""
    db_element = database.query(Element).filter(Element.id == element_id).first()
    if db_element is None:
        raise HTTPException(status_code=404, detail="Element not found")

    # Check if relationship exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.ref == element_id) &
        (evaluation_element.c.eval == evaluation_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = evaluation_element.delete().where(
        (evaluation_element.c.ref == element_id) &
        (evaluation_element.c.eval == evaluation_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Evaluation removed from eval successfully"}


@app.get("/element/{element_id}/eval/", response_model=None, tags=["Element Relationships"])
async def get_eval_of_element(element_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this Element through eval"""
    db_element = database.query(Element).filter(Element.id == element_id).first()
    if db_element is None:
        raise HTTPException(status_code=404, detail="Element not found")

    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == element_id).all()
    evaluation_list = database.query(Evaluation).filter(Evaluation.id.in_([id[0] for id in evaluation_ids])).all()

    return {
        "element_id": element_id,
        "eval_count": len(evaluation_list),
        "eval": evaluation_list
    }


@app.get("/element/{element_id}/measure/", response_model=None, tags=["Element Relationships"])
async def get_measure_of_element(element_id: int, database: Session = Depends(get_db)):
    """Get all Measure entities related to this Element through measure"""
    db_element = database.query(Element).filter(Element.id == element_id).first()
    if db_element is None:
        raise HTTPException(status_code=404, detail="Element not found")

    measure_list = database.query(Measure).filter(Measure.measurand_id == element_id).all()

    return {
        "element_id": element_id,
        "measure_count": len(measure_list),
        "measure": measure_list
    }

@app.get("/element/{element_id}/evalu/", response_model=None, tags=["Element Relationships"])
async def get_evalu_of_element(element_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this Element through evalu"""
    db_element = database.query(Element).filter(Element.id == element_id).first()
    if db_element is None:
        raise HTTPException(status_code=404, detail="Element not found")

    evalu_list = database.query(Evaluation).filter(Evaluation.evaluates_id == element_id).all()

    return {
        "element_id": element_id,
        "evalu_count": len(evalu_list),
        "evalu": evalu_list
    }





############################################
#
#   Dataset functions
#
############################################

@app.get("/dataset/", response_model=None, tags=["Dataset"])
def get_all_dataset(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Dataset)
        query = query.options(joinedload(Dataset.datashape))
        query = query.options(joinedload(Dataset.project))
        dataset_list = query.all()

        # Serialize with relationships included
        result = []
        for dataset_item in dataset_list:
            item_dict = dataset_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if dataset_item.datashape:
                related_obj = dataset_item.datashape
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['datashape'] = related_dict
            else:
                item_dict['datashape'] = None
            if dataset_item.project:
                related_obj = dataset_item.project
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['project'] = related_dict
            else:
                item_dict['project'] = None

            # Add many-to-many and one-to-many relationship objects (full details)
            aisystem_list = database.query(AISystem).join(aisystem_dataset, AISystem.id == aisystem_dataset.c.models).filter(aisystem_dataset.c.dataset == dataset_item.id).all()
            item_dict['models'] = []
            for aisystem_obj in aisystem_list:
                aisystem_dict = aisystem_obj.__dict__.copy()
                aisystem_dict.pop('_sa_instance_state', None)
                item_dict['models'].append(aisystem_dict)
            evaluation_list = database.query(Evaluation).join(evaluation_element, Evaluation.id == evaluation_element.c.eval).filter(evaluation_element.c.ref == dataset_item.id).all()
            item_dict['eval'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['eval'].append(evaluation_dict)
            observation_list = database.query(Observation).filter(Observation.dataset_id == dataset_item.id).all()
            item_dict['observation_2'] = []
            for observation_obj in observation_list:
                observation_dict = observation_obj.__dict__.copy()
                observation_dict.pop('_sa_instance_state', None)
                item_dict['observation_2'].append(observation_dict)
            measure_list = database.query(Measure).filter(Measure.measurand_id == dataset_item.id).all()
            item_dict['measure'] = []
            for measure_obj in measure_list:
                measure_dict = measure_obj.__dict__.copy()
                measure_dict.pop('_sa_instance_state', None)
                item_dict['measure'].append(measure_dict)
            evaluation_list = database.query(Evaluation).filter(Evaluation.evaluates_id == dataset_item.id).all()
            item_dict['evalu'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['evalu'].append(evaluation_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Dataset).all()


@app.get("/dataset/count/", response_model=None, tags=["Dataset"])
def get_count_dataset(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Dataset entities"""
    count = database.query(Dataset).count()
    return {"count": count}


@app.get("/dataset/paginated/", response_model=None, tags=["Dataset"])
def get_paginated_dataset(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Dataset entities"""
    total = database.query(Dataset).count()
    dataset_list = database.query(Dataset).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": dataset_list
        }

    result = []
    for dataset_item in dataset_list:
        aisystem_ids = database.query(aisystem_dataset.c.models).filter(aisystem_dataset.c.dataset == dataset_item.id).all()
        evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == dataset_item.id).all()
        observation_2_ids = database.query(Observation.id).filter(Observation.dataset_id == dataset_item.id).all()
        measure_ids = database.query(Measure.id).filter(Measure.measurand_id == dataset_item.id).all()
        evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == dataset_item.id).all()
        item_data = {
            "dataset": dataset_item,
            "aisystem_ids": [x[0] for x in aisystem_ids],
            "evaluation_ids": [x[0] for x in evaluation_ids],
            "observation_2_ids": [x[0] for x in observation_2_ids],            "measure_ids": [x[0] for x in measure_ids],            "evalu_ids": [x[0] for x in evalu_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/dataset/search/", response_model=None, tags=["Dataset"])
def search_dataset(
    database: Session = Depends(get_db)
) -> list:
    """Search Dataset entities by attributes"""
    query = database.query(Dataset)


    results = query.all()
    return results


@app.get("/dataset/{dataset_id}/", response_model=None, tags=["Dataset"])
async def get_dataset(dataset_id: int, database: Session = Depends(get_db)) -> Dataset:
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    aisystem_ids = database.query(aisystem_dataset.c.models).filter(aisystem_dataset.c.dataset == db_dataset.id).all()
    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_dataset.id).all()
    observation_2_ids = database.query(Observation.id).filter(Observation.dataset_id == db_dataset.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_dataset.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_dataset.id).all()
    response_data = {
        "dataset": db_dataset,
        "aisystem_ids": [x[0] for x in aisystem_ids],
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "observation_2_ids": [x[0] for x in observation_2_ids],        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]}
    return response_data



@app.post("/dataset/", response_model=None, tags=["Dataset"])
async def create_dataset(dataset_data: DatasetCreate, database: Session = Depends(get_db)) -> Dataset:

    if dataset_data.datashape is not None:
        db_datashape = database.query(Datashape).filter(Datashape.id == dataset_data.datashape).first()
        if not db_datashape:
            raise HTTPException(status_code=400, detail="Datashape not found")
    else:
        raise HTTPException(status_code=400, detail="Datashape ID is required")
    if dataset_data.project :
        db_project = database.query(Project).filter(Project.id == dataset_data.project).first()
        if not db_project:
            raise HTTPException(status_code=400, detail="Project not found")
    if dataset_data.models:
        for id in dataset_data.models:
            # Entity already validated before creation
            db_aisystem = database.query(AISystem).filter(AISystem.id == id).first()
            if not db_aisystem:
                raise HTTPException(status_code=404, detail=f"AISystem with ID {id} not found")
    if dataset_data.eval:
        for id in dataset_data.eval:
            # Entity already validated before creation
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == id).first()
            if not db_evaluation:
                raise HTTPException(status_code=404, detail=f"Evaluation with ID {id} not found")

    db_dataset = Dataset(
        name=dataset_data.name,        description=dataset_data.description,        source=dataset_data.source,        licensing=dataset_data.licensing.value,        version=dataset_data.version,        dataset_type=dataset_data.dataset_type.value,        datashape_id=dataset_data.datashape,        project_id=dataset_data.project        )

    database.add(db_dataset)
    database.commit()
    database.refresh(db_dataset)

    if dataset_data.observation_2:
        # Validate that all Observation IDs exist
        for observation_id in dataset_data.observation_2:
            db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
            if not db_observation:
                raise HTTPException(status_code=400, detail=f"Observation with id {observation_id} not found")

        # Update the related entities with the new foreign key
        database.query(Observation).filter(Observation.id.in_(dataset_data.observation_2)).update(
            {Observation.dataset_id: db_dataset.id}, synchronize_session=False
        )
        database.commit()
    if dataset_data.measure:
        # Validate that all Measure IDs exist
        for measure_id in dataset_data.measure:
            db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
            if not db_measure:
                raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

        # Update the related entities with the new foreign key
        database.query(Measure).filter(Measure.id.in_(dataset_data.measure)).update(
            {Measure.measurand_id: db_dataset.id}, synchronize_session=False
        )
        database.commit()
    if dataset_data.evalu:
        # Validate that all Evaluation IDs exist
        for evaluation_id in dataset_data.evalu:
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not db_evaluation:
                raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

        # Update the related entities with the new foreign key
        database.query(Evaluation).filter(Evaluation.id.in_(dataset_data.evalu)).update(
            {Evaluation.evaluates_id: db_dataset.id}, synchronize_session=False
        )
        database.commit()

    if dataset_data.models:
        for id in dataset_data.models:
            # Entity already validated before creation
            db_aisystem = database.query(AISystem).filter(AISystem.id == id).first()
            # Create the association
            association = aisystem_dataset.insert().values(dataset=db_dataset.id, models=db_aisystem.id)
            database.execute(association)
            database.commit()
    if dataset_data.eval:
        for id in dataset_data.eval:
            # Entity already validated before creation
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == id).first()
            # Create the association
            association = evaluation_element.insert().values(ref=db_dataset.id, eval=db_evaluation.id)
            database.execute(association)
            database.commit()


    aisystem_ids = database.query(aisystem_dataset.c.models).filter(aisystem_dataset.c.dataset == db_dataset.id).all()
    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_dataset.id).all()
    observation_2_ids = database.query(Observation.id).filter(Observation.dataset_id == db_dataset.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_dataset.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_dataset.id).all()
    response_data = {
        "dataset": db_dataset,
        "aisystem_ids": [x[0] for x in aisystem_ids],
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "observation_2_ids": [x[0] for x in observation_2_ids],        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]    }
    return response_data


@app.post("/dataset/bulk/", response_model=None, tags=["Dataset"])
async def bulk_create_dataset(items: list[DatasetCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Dataset entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.datashape:
                raise ValueError("Datashape ID is required")

            db_dataset = Dataset(
                name=item_data.name,                description=item_data.description,                source=item_data.source,                licensing=item_data.licensing.value,                version=item_data.version,                dataset_type=item_data.dataset_type.value,                datashape_id=item_data.datashape,                project_id=item_data.project            )
            database.add(db_dataset)
            database.flush()  # Get ID without committing
            created_items.append(db_dataset.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Dataset entities"
    }


@app.delete("/dataset/bulk/", response_model=None, tags=["Dataset"])
async def bulk_delete_dataset(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Dataset entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_dataset = database.query(Dataset).filter(Dataset.id == item_id).first()
        if db_dataset:
            database.delete(db_dataset)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Dataset entities"
    }

@app.put("/dataset/{dataset_id}/", response_model=None, tags=["Dataset"])
async def update_dataset(dataset_id: int, dataset_data: DatasetCreate, database: Session = Depends(get_db)) -> Dataset:
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    setattr(db_dataset, 'source', dataset_data.source)
    setattr(db_dataset, 'licensing', dataset_data.licensing.value)
    setattr(db_dataset, 'version', dataset_data.version)
    setattr(db_dataset, 'dataset_type', dataset_data.dataset_type.value)
    if dataset_data.datashape is not None:
        db_datashape = database.query(Datashape).filter(Datashape.id == dataset_data.datashape).first()
        if not db_datashape:
            raise HTTPException(status_code=400, detail="Datashape not found")
        setattr(db_dataset, 'datashape_id', dataset_data.datashape)
    if dataset_data.observation_2 is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Observation).filter(Observation.dataset_id == db_dataset.id).update(
            {Observation.dataset_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if dataset_data.observation_2:
            # Validate that all IDs exist
            for observation_id in dataset_data.observation_2:
                db_observation = database.query(Observation).filter(Observation.id == observation_id).first()
                if not db_observation:
                    raise HTTPException(status_code=400, detail=f"Observation with id {observation_id} not found")

            # Update the related entities with the new foreign key
            database.query(Observation).filter(Observation.id.in_(dataset_data.observation_2)).update(
                {Observation.dataset_id: db_dataset.id}, synchronize_session=False
            )
    if dataset_data.measure is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Measure).filter(Measure.measurand_id == db_dataset.id).update(
            {Measure.measurand_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if dataset_data.measure:
            # Validate that all IDs exist
            for measure_id in dataset_data.measure:
                db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
                if not db_measure:
                    raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

            # Update the related entities with the new foreign key
            database.query(Measure).filter(Measure.id.in_(dataset_data.measure)).update(
                {Measure.measurand_id: db_dataset.id}, synchronize_session=False
            )
    if dataset_data.evalu is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Evaluation).filter(Evaluation.evaluates_id == db_dataset.id).update(
            {Evaluation.evaluates_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if dataset_data.evalu:
            # Validate that all IDs exist
            for evaluation_id in dataset_data.evalu:
                db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
                if not db_evaluation:
                    raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

            # Update the related entities with the new foreign key
            database.query(Evaluation).filter(Evaluation.id.in_(dataset_data.evalu)).update(
                {Evaluation.evaluates_id: db_dataset.id}, synchronize_session=False
            )
    existing_aisystem_ids = [assoc.models for assoc in database.execute(
        aisystem_dataset.select().where(aisystem_dataset.c.dataset == db_dataset.id))]

    aisystems_to_remove = set(existing_aisystem_ids) - set(dataset_data.models)
    for aisystem_id in aisystems_to_remove:
        association = aisystem_dataset.delete().where(
            (aisystem_dataset.c.dataset == db_dataset.id) & (aisystem_dataset.c.models == aisystem_id))
        database.execute(association)

    new_aisystem_ids = set(dataset_data.models) - set(existing_aisystem_ids)
    for aisystem_id in new_aisystem_ids:
        db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
        if db_aisystem is None:
            raise HTTPException(status_code=404, detail=f"AISystem with ID {aisystem_id} not found")
        association = aisystem_dataset.insert().values(models=db_aisystem.id, dataset=db_dataset.id)
        database.execute(association)
    existing_evaluation_ids = [assoc.eval for assoc in database.execute(
        evaluation_element.select().where(evaluation_element.c.ref == db_dataset.id))]

    evaluations_to_remove = set(existing_evaluation_ids) - set(dataset_data.eval)
    for evaluation_id in evaluations_to_remove:
        association = evaluation_element.delete().where(
            (evaluation_element.c.ref == db_dataset.id) & (evaluation_element.c.eval == evaluation_id))
        database.execute(association)

    new_evaluation_ids = set(dataset_data.eval) - set(existing_evaluation_ids)
    for evaluation_id in new_evaluation_ids:
        db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if db_evaluation is None:
            raise HTTPException(status_code=404, detail=f"Evaluation with ID {evaluation_id} not found")
        association = evaluation_element.insert().values(eval=db_evaluation.id, ref=db_dataset.id)
        database.execute(association)
    database.commit()
    database.refresh(db_dataset)

    aisystem_ids = database.query(aisystem_dataset.c.models).filter(aisystem_dataset.c.dataset == db_dataset.id).all()
    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_dataset.id).all()
    observation_2_ids = database.query(Observation.id).filter(Observation.dataset_id == db_dataset.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_dataset.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_dataset.id).all()
    response_data = {
        "dataset": db_dataset,
        "aisystem_ids": [x[0] for x in aisystem_ids],
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "observation_2_ids": [x[0] for x in observation_2_ids],        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]    }
    return response_data


@app.delete("/dataset/{dataset_id}/", response_model=None, tags=["Dataset"])
async def delete_dataset(dataset_id: int, database: Session = Depends(get_db)):
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    database.delete(db_dataset)
    database.commit()
    return db_dataset

@app.post("/dataset/{dataset_id}/models/{aisystem_id}/", response_model=None, tags=["Dataset Relationships"])
async def add_models_to_dataset(dataset_id: int, aisystem_id: int, database: Session = Depends(get_db)):
    """Add a AISystem to this Dataset's models relationship"""
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    # Check if relationship already exists
    existing = database.query(aisystem_dataset).filter(
        (aisystem_dataset.c.dataset == dataset_id) &
        (aisystem_dataset.c.models == aisystem_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = aisystem_dataset.insert().values(dataset=dataset_id, models=aisystem_id)
    database.execute(association)
    database.commit()

    return {"message": "AISystem added to models successfully"}


@app.delete("/dataset/{dataset_id}/models/{aisystem_id}/", response_model=None, tags=["Dataset Relationships"])
async def remove_models_from_dataset(dataset_id: int, aisystem_id: int, database: Session = Depends(get_db)):
    """Remove a AISystem from this Dataset's models relationship"""
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Check if relationship exists
    existing = database.query(aisystem_dataset).filter(
        (aisystem_dataset.c.dataset == dataset_id) &
        (aisystem_dataset.c.models == aisystem_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = aisystem_dataset.delete().where(
        (aisystem_dataset.c.dataset == dataset_id) &
        (aisystem_dataset.c.models == aisystem_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "AISystem removed from models successfully"}


@app.get("/dataset/{dataset_id}/models/", response_model=None, tags=["Dataset Relationships"])
async def get_models_of_dataset(dataset_id: int, database: Session = Depends(get_db)):
    """Get all AISystem entities related to this Dataset through models"""
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    aisystem_ids = database.query(aisystem_dataset.c.models).filter(aisystem_dataset.c.dataset == dataset_id).all()
    aisystem_list = database.query(AISystem).filter(AISystem.id.in_([id[0] for id in aisystem_ids])).all()

    return {
        "dataset_id": dataset_id,
        "models_count": len(aisystem_list),
        "models": aisystem_list
    }

@app.post("/dataset/{dataset_id}/eval/{evaluation_id}/", response_model=None, tags=["Dataset Relationships"])
async def add_eval_to_dataset(dataset_id: int, evaluation_id: int, database: Session = Depends(get_db)):
    """Add a Evaluation to this Dataset's eval relationship"""
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Check if relationship already exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.ref == dataset_id) &
        (evaluation_element.c.eval == evaluation_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = evaluation_element.insert().values(ref=dataset_id, eval=evaluation_id)
    database.execute(association)
    database.commit()

    return {"message": "Evaluation added to eval successfully"}


@app.delete("/dataset/{dataset_id}/eval/{evaluation_id}/", response_model=None, tags=["Dataset Relationships"])
async def remove_eval_from_dataset(dataset_id: int, evaluation_id: int, database: Session = Depends(get_db)):
    """Remove a Evaluation from this Dataset's eval relationship"""
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Check if relationship exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.ref == dataset_id) &
        (evaluation_element.c.eval == evaluation_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = evaluation_element.delete().where(
        (evaluation_element.c.ref == dataset_id) &
        (evaluation_element.c.eval == evaluation_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Evaluation removed from eval successfully"}


@app.get("/dataset/{dataset_id}/eval/", response_model=None, tags=["Dataset Relationships"])
async def get_eval_of_dataset(dataset_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this Dataset through eval"""
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == dataset_id).all()
    evaluation_list = database.query(Evaluation).filter(Evaluation.id.in_([id[0] for id in evaluation_ids])).all()

    return {
        "dataset_id": dataset_id,
        "eval_count": len(evaluation_list),
        "eval": evaluation_list
    }


@app.get("/dataset/{dataset_id}/observation_2/", response_model=None, tags=["Dataset Relationships"])
async def get_observation_2_of_dataset(dataset_id: int, database: Session = Depends(get_db)):
    """Get all Observation entities related to this Dataset through observation_2"""
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    observation_2_list = database.query(Observation).filter(Observation.dataset_id == dataset_id).all()

    return {
        "dataset_id": dataset_id,
        "observation_2_count": len(observation_2_list),
        "observation_2": observation_2_list
    }

@app.get("/dataset/{dataset_id}/measure/", response_model=None, tags=["Dataset Relationships"])
async def get_measure_of_dataset(dataset_id: int, database: Session = Depends(get_db)):
    """Get all Measure entities related to this Dataset through measure"""
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    measure_list = database.query(Measure).filter(Measure.measurand_id == dataset_id).all()

    return {
        "dataset_id": dataset_id,
        "measure_count": len(measure_list),
        "measure": measure_list
    }

@app.get("/dataset/{dataset_id}/evalu/", response_model=None, tags=["Dataset Relationships"])
async def get_evalu_of_dataset(dataset_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this Dataset through evalu"""
    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    evalu_list = database.query(Evaluation).filter(Evaluation.evaluates_id == dataset_id).all()

    return {
        "dataset_id": dataset_id,
        "evalu_count": len(evalu_list),
        "evalu": evalu_list
    }





############################################
#
#   Feature functions
#
############################################

@app.get("/feature/", response_model=None, tags=["Feature"])
def get_all_feature(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Feature)
        query = query.options(joinedload(Feature.features))
        query = query.options(joinedload(Feature.project))
        feature_list = query.all()

        # Serialize with relationships included
        result = []
        for feature_item in feature_list:
            item_dict = feature_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if feature_item.features:
                related_obj = feature_item.features
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['features'] = related_dict
            else:
                item_dict['features'] = None
            if feature_item.project:
                related_obj = feature_item.project
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['project'] = related_dict
            else:
                item_dict['project'] = None

            # Add many-to-many and one-to-many relationship objects (full details)
            datashape_list = database.query(Datashape).join(datashape_feature, Datashape.id == datashape_feature.c.date).filter(datashape_feature.c.f_date == feature_item.id).all()
            item_dict['date'] = []
            for datashape_obj in datashape_list:
                datashape_dict = datashape_obj.__dict__.copy()
                datashape_dict.pop('_sa_instance_state', None)
                item_dict['date'].append(datashape_dict)
            evaluation_list = database.query(Evaluation).join(evaluation_element, Evaluation.id == evaluation_element.c.eval).filter(evaluation_element.c.ref == feature_item.id).all()
            item_dict['eval'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['eval'].append(evaluation_dict)
            measure_list = database.query(Measure).filter(Measure.measurand_id == feature_item.id).all()
            item_dict['measure'] = []
            for measure_obj in measure_list:
                measure_dict = measure_obj.__dict__.copy()
                measure_dict.pop('_sa_instance_state', None)
                item_dict['measure'].append(measure_dict)
            evaluation_list = database.query(Evaluation).filter(Evaluation.evaluates_id == feature_item.id).all()
            item_dict['evalu'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['evalu'].append(evaluation_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Feature).all()


@app.get("/feature/count/", response_model=None, tags=["Feature"])
def get_count_feature(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Feature entities"""
    count = database.query(Feature).count()
    return {"count": count}


@app.get("/feature/paginated/", response_model=None, tags=["Feature"])
def get_paginated_feature(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Feature entities"""
    total = database.query(Feature).count()
    feature_list = database.query(Feature).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": feature_list
        }

    result = []
    for feature_item in feature_list:
        datashape_ids = database.query(datashape_feature.c.date).filter(datashape_feature.c.f_date == feature_item.id).all()
        evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == feature_item.id).all()
        measure_ids = database.query(Measure.id).filter(Measure.measurand_id == feature_item.id).all()
        evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == feature_item.id).all()
        item_data = {
            "feature": feature_item,
            "datashape_ids": [x[0] for x in datashape_ids],
            "evaluation_ids": [x[0] for x in evaluation_ids],
            "measure_ids": [x[0] for x in measure_ids],            "evalu_ids": [x[0] for x in evalu_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/feature/search/", response_model=None, tags=["Feature"])
def search_feature(
    database: Session = Depends(get_db)
) -> list:
    """Search Feature entities by attributes"""
    query = database.query(Feature)


    results = query.all()
    return results


@app.get("/feature/{feature_id}/", response_model=None, tags=["Feature"])
async def get_feature(feature_id: int, database: Session = Depends(get_db)) -> Feature:
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    datashape_ids = database.query(datashape_feature.c.date).filter(datashape_feature.c.f_date == db_feature.id).all()
    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_feature.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_feature.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_feature.id).all()
    response_data = {
        "feature": db_feature,
        "datashape_ids": [x[0] for x in datashape_ids],
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]}
    return response_data



@app.post("/feature/", response_model=None, tags=["Feature"])
async def create_feature(feature_data: FeatureCreate, database: Session = Depends(get_db)) -> Feature:

    if feature_data.features is not None:
        db_features = database.query(Datashape).filter(Datashape.id == feature_data.features).first()
        if not db_features:
            raise HTTPException(status_code=400, detail="Datashape not found")
    else:
        raise HTTPException(status_code=400, detail="Datashape ID is required")
    if feature_data.project :
        db_project = database.query(Project).filter(Project.id == feature_data.project).first()
        if not db_project:
            raise HTTPException(status_code=400, detail="Project not found")
    if feature_data.date:
        for id in feature_data.date:
            # Entity already validated before creation
            db_datashape = database.query(Datashape).filter(Datashape.id == id).first()
            if not db_datashape:
                raise HTTPException(status_code=404, detail=f"Datashape with ID {id} not found")
    if feature_data.eval:
        for id in feature_data.eval:
            # Entity already validated before creation
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == id).first()
            if not db_evaluation:
                raise HTTPException(status_code=404, detail=f"Evaluation with ID {id} not found")

    db_feature = Feature(
        name=feature_data.name,        description=feature_data.description,        max_value=feature_data.max_value,        feature_type=feature_data.feature_type,        min_value=feature_data.min_value,        features_id=feature_data.features,        project_id=feature_data.project        )

    database.add(db_feature)
    database.commit()
    database.refresh(db_feature)

    if feature_data.measure:
        # Validate that all Measure IDs exist
        for measure_id in feature_data.measure:
            db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
            if not db_measure:
                raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

        # Update the related entities with the new foreign key
        database.query(Measure).filter(Measure.id.in_(feature_data.measure)).update(
            {Measure.measurand_id: db_feature.id}, synchronize_session=False
        )
        database.commit()
    if feature_data.evalu:
        # Validate that all Evaluation IDs exist
        for evaluation_id in feature_data.evalu:
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not db_evaluation:
                raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

        # Update the related entities with the new foreign key
        database.query(Evaluation).filter(Evaluation.id.in_(feature_data.evalu)).update(
            {Evaluation.evaluates_id: db_feature.id}, synchronize_session=False
        )
        database.commit()

    if feature_data.date:
        for id in feature_data.date:
            # Entity already validated before creation
            db_datashape = database.query(Datashape).filter(Datashape.id == id).first()
            # Create the association
            association = datashape_feature.insert().values(f_date=db_feature.id, date=db_datashape.id)
            database.execute(association)
            database.commit()
    if feature_data.eval:
        for id in feature_data.eval:
            # Entity already validated before creation
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == id).first()
            # Create the association
            association = evaluation_element.insert().values(ref=db_feature.id, eval=db_evaluation.id)
            database.execute(association)
            database.commit()


    datashape_ids = database.query(datashape_feature.c.date).filter(datashape_feature.c.f_date == db_feature.id).all()
    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_feature.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_feature.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_feature.id).all()
    response_data = {
        "feature": db_feature,
        "datashape_ids": [x[0] for x in datashape_ids],
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]    }
    return response_data


@app.post("/feature/bulk/", response_model=None, tags=["Feature"])
async def bulk_create_feature(items: list[FeatureCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Feature entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.features:
                raise ValueError("Datashape ID is required")

            db_feature = Feature(
                name=item_data.name,                description=item_data.description,                max_value=item_data.max_value,                feature_type=item_data.feature_type,                min_value=item_data.min_value,                features_id=item_data.features,                project_id=item_data.project            )
            database.add(db_feature)
            database.flush()  # Get ID without committing
            created_items.append(db_feature.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Feature entities"
    }


@app.delete("/feature/bulk/", response_model=None, tags=["Feature"])
async def bulk_delete_feature(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Feature entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_feature = database.query(Feature).filter(Feature.id == item_id).first()
        if db_feature:
            database.delete(db_feature)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Feature entities"
    }

@app.put("/feature/{feature_id}/", response_model=None, tags=["Feature"])
async def update_feature(feature_id: int, feature_data: FeatureCreate, database: Session = Depends(get_db)) -> Feature:
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    setattr(db_feature, 'max_value', feature_data.max_value)
    setattr(db_feature, 'feature_type', feature_data.feature_type)
    setattr(db_feature, 'min_value', feature_data.min_value)
    if feature_data.features is not None:
        db_features = database.query(Datashape).filter(Datashape.id == feature_data.features).first()
        if not db_features:
            raise HTTPException(status_code=400, detail="Datashape not found")
        setattr(db_feature, 'features_id', feature_data.features)
    if feature_data.measure is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Measure).filter(Measure.measurand_id == db_feature.id).update(
            {Measure.measurand_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if feature_data.measure:
            # Validate that all IDs exist
            for measure_id in feature_data.measure:
                db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
                if not db_measure:
                    raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

            # Update the related entities with the new foreign key
            database.query(Measure).filter(Measure.id.in_(feature_data.measure)).update(
                {Measure.measurand_id: db_feature.id}, synchronize_session=False
            )
    if feature_data.evalu is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Evaluation).filter(Evaluation.evaluates_id == db_feature.id).update(
            {Evaluation.evaluates_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if feature_data.evalu:
            # Validate that all IDs exist
            for evaluation_id in feature_data.evalu:
                db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
                if not db_evaluation:
                    raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

            # Update the related entities with the new foreign key
            database.query(Evaluation).filter(Evaluation.id.in_(feature_data.evalu)).update(
                {Evaluation.evaluates_id: db_feature.id}, synchronize_session=False
            )
    existing_datashape_ids = [assoc.date for assoc in database.execute(
        datashape_feature.select().where(datashape_feature.c.f_date == db_feature.id))]

    datashapes_to_remove = set(existing_datashape_ids) - set(feature_data.date)
    for datashape_id in datashapes_to_remove:
        association = datashape_feature.delete().where(
            (datashape_feature.c.f_date == db_feature.id) & (datashape_feature.c.date == datashape_id))
        database.execute(association)

    new_datashape_ids = set(feature_data.date) - set(existing_datashape_ids)
    for datashape_id in new_datashape_ids:
        db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
        if db_datashape is None:
            raise HTTPException(status_code=404, detail=f"Datashape with ID {datashape_id} not found")
        association = datashape_feature.insert().values(date=db_datashape.id, f_date=db_feature.id)
        database.execute(association)
    existing_evaluation_ids = [assoc.eval for assoc in database.execute(
        evaluation_element.select().where(evaluation_element.c.ref == db_feature.id))]

    evaluations_to_remove = set(existing_evaluation_ids) - set(feature_data.eval)
    for evaluation_id in evaluations_to_remove:
        association = evaluation_element.delete().where(
            (evaluation_element.c.ref == db_feature.id) & (evaluation_element.c.eval == evaluation_id))
        database.execute(association)

    new_evaluation_ids = set(feature_data.eval) - set(existing_evaluation_ids)
    for evaluation_id in new_evaluation_ids:
        db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if db_evaluation is None:
            raise HTTPException(status_code=404, detail=f"Evaluation with ID {evaluation_id} not found")
        association = evaluation_element.insert().values(eval=db_evaluation.id, ref=db_feature.id)
        database.execute(association)
    database.commit()
    database.refresh(db_feature)

    datashape_ids = database.query(datashape_feature.c.date).filter(datashape_feature.c.f_date == db_feature.id).all()
    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_feature.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_feature.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_feature.id).all()
    response_data = {
        "feature": db_feature,
        "datashape_ids": [x[0] for x in datashape_ids],
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]    }
    return response_data


@app.delete("/feature/{feature_id}/", response_model=None, tags=["Feature"])
async def delete_feature(feature_id: int, database: Session = Depends(get_db)):
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    database.delete(db_feature)
    database.commit()
    return db_feature

@app.post("/feature/{feature_id}/date/{datashape_id}/", response_model=None, tags=["Feature Relationships"])
async def add_date_to_feature(feature_id: int, datashape_id: int, database: Session = Depends(get_db)):
    """Add a Datashape to this Feature's date relationship"""
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    db_datashape = database.query(Datashape).filter(Datashape.id == datashape_id).first()
    if db_datashape is None:
        raise HTTPException(status_code=404, detail="Datashape not found")

    # Check if relationship already exists
    existing = database.query(datashape_feature).filter(
        (datashape_feature.c.f_date == feature_id) &
        (datashape_feature.c.date == datashape_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = datashape_feature.insert().values(f_date=feature_id, date=datashape_id)
    database.execute(association)
    database.commit()

    return {"message": "Datashape added to date successfully"}


@app.delete("/feature/{feature_id}/date/{datashape_id}/", response_model=None, tags=["Feature Relationships"])
async def remove_date_from_feature(feature_id: int, datashape_id: int, database: Session = Depends(get_db)):
    """Remove a Datashape from this Feature's date relationship"""
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Check if relationship exists
    existing = database.query(datashape_feature).filter(
        (datashape_feature.c.f_date == feature_id) &
        (datashape_feature.c.date == datashape_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = datashape_feature.delete().where(
        (datashape_feature.c.f_date == feature_id) &
        (datashape_feature.c.date == datashape_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Datashape removed from date successfully"}


@app.get("/feature/{feature_id}/date/", response_model=None, tags=["Feature Relationships"])
async def get_date_of_feature(feature_id: int, database: Session = Depends(get_db)):
    """Get all Datashape entities related to this Feature through date"""
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    datashape_ids = database.query(datashape_feature.c.date).filter(datashape_feature.c.f_date == feature_id).all()
    datashape_list = database.query(Datashape).filter(Datashape.id.in_([id[0] for id in datashape_ids])).all()

    return {
        "feature_id": feature_id,
        "date_count": len(datashape_list),
        "date": datashape_list
    }

@app.post("/feature/{feature_id}/eval/{evaluation_id}/", response_model=None, tags=["Feature Relationships"])
async def add_eval_to_feature(feature_id: int, evaluation_id: int, database: Session = Depends(get_db)):
    """Add a Evaluation to this Feature's eval relationship"""
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Check if relationship already exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.ref == feature_id) &
        (evaluation_element.c.eval == evaluation_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = evaluation_element.insert().values(ref=feature_id, eval=evaluation_id)
    database.execute(association)
    database.commit()

    return {"message": "Evaluation added to eval successfully"}


@app.delete("/feature/{feature_id}/eval/{evaluation_id}/", response_model=None, tags=["Feature Relationships"])
async def remove_eval_from_feature(feature_id: int, evaluation_id: int, database: Session = Depends(get_db)):
    """Remove a Evaluation from this Feature's eval relationship"""
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Check if relationship exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.ref == feature_id) &
        (evaluation_element.c.eval == evaluation_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = evaluation_element.delete().where(
        (evaluation_element.c.ref == feature_id) &
        (evaluation_element.c.eval == evaluation_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Evaluation removed from eval successfully"}


@app.get("/feature/{feature_id}/eval/", response_model=None, tags=["Feature Relationships"])
async def get_eval_of_feature(feature_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this Feature through eval"""
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == feature_id).all()
    evaluation_list = database.query(Evaluation).filter(Evaluation.id.in_([id[0] for id in evaluation_ids])).all()

    return {
        "feature_id": feature_id,
        "eval_count": len(evaluation_list),
        "eval": evaluation_list
    }


@app.get("/feature/{feature_id}/measure/", response_model=None, tags=["Feature Relationships"])
async def get_measure_of_feature(feature_id: int, database: Session = Depends(get_db)):
    """Get all Measure entities related to this Feature through measure"""
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    measure_list = database.query(Measure).filter(Measure.measurand_id == feature_id).all()

    return {
        "feature_id": feature_id,
        "measure_count": len(measure_list),
        "measure": measure_list
    }

@app.get("/feature/{feature_id}/evalu/", response_model=None, tags=["Feature Relationships"])
async def get_evalu_of_feature(feature_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this Feature through evalu"""
    db_feature = database.query(Feature).filter(Feature.id == feature_id).first()
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    evalu_list = database.query(Evaluation).filter(Evaluation.evaluates_id == feature_id).all()

    return {
        "feature_id": feature_id,
        "evalu_count": len(evalu_list),
        "evalu": evalu_list
    }





############################################
#
#   AISystem functions
#
############################################

@app.get("/aisystem/", response_model=None, tags=["AISystem"])
def get_all_aisystem(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(AISystem)
        query = query.options(joinedload(AISystem.project))
        aisystem_list = query.all()

        # Serialize with relationships included
        result = []
        for aisystem_item in aisystem_list:
            item_dict = aisystem_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if aisystem_item.project:
                related_obj = aisystem_item.project
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['project'] = related_dict
            else:
                item_dict['project'] = None

            # Add many-to-many and one-to-many relationship objects (full details)
            dataset_list = database.query(Dataset).join(aisystem_dataset, Dataset.id == aisystem_dataset.c.dataset).filter(aisystem_dataset.c.models == aisystem_item.id).all()
            item_dict['dataset'] = []
            for dataset_obj in dataset_list:
                dataset_dict = dataset_obj.__dict__.copy()
                dataset_dict.pop('_sa_instance_state', None)
                item_dict['dataset'].append(dataset_dict)
            evaluation_list = database.query(Evaluation).join(evaluation_element, Evaluation.id == evaluation_element.c.eval).filter(evaluation_element.c.ref == aisystem_item.id).all()
            item_dict['eval'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['eval'].append(evaluation_dict)
            measure_list = database.query(Measure).filter(Measure.measurand_id == aisystem_item.id).all()
            item_dict['measure'] = []
            for measure_obj in measure_list:
                measure_dict = measure_obj.__dict__.copy()
                measure_dict.pop('_sa_instance_state', None)
                item_dict['measure'].append(measure_dict)
            evaluation_list = database.query(Evaluation).filter(Evaluation.evaluates_id == aisystem_item.id).all()
            item_dict['evalu'] = []
            for evaluation_obj in evaluation_list:
                evaluation_dict = evaluation_obj.__dict__.copy()
                evaluation_dict.pop('_sa_instance_state', None)
                item_dict['evalu'].append(evaluation_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(AISystem).all()


@app.get("/aisystem/count/", response_model=None, tags=["AISystem"])
def get_count_aisystem(database: Session = Depends(get_db)) -> dict:
    """Get the total count of AISystem entities"""
    count = database.query(AISystem).count()
    return {"count": count}


@app.get("/aisystem/paginated/", response_model=None, tags=["AISystem"])
def get_paginated_aisystem(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of AISystem entities"""
    total = database.query(AISystem).count()
    aisystem_list = database.query(AISystem).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": aisystem_list
        }

    result = []
    for aisystem_item in aisystem_list:
        dataset_ids = database.query(aisystem_dataset.c.dataset).filter(aisystem_dataset.c.models == aisystem_item.id).all()
        evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == aisystem_item.id).all()
        measure_ids = database.query(Measure.id).filter(Measure.measurand_id == aisystem_item.id).all()
        evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == aisystem_item.id).all()
        item_data = {
            "aisystem": aisystem_item,
            "dataset_ids": [x[0] for x in dataset_ids],
            "evaluation_ids": [x[0] for x in evaluation_ids],
            "measure_ids": [x[0] for x in measure_ids],            "evalu_ids": [x[0] for x in evalu_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/aisystem/search/", response_model=None, tags=["AISystem"])
def search_aisystem(
    database: Session = Depends(get_db)
) -> list:
    """Search AISystem entities by attributes"""
    query = database.query(AISystem)


    results = query.all()
    return results


@app.get("/aisystem/{aisystem_id}/", response_model=None, tags=["AISystem"])
async def get_aisystem(aisystem_id: int, database: Session = Depends(get_db)) -> AISystem:
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    dataset_ids = database.query(aisystem_dataset.c.dataset).filter(aisystem_dataset.c.models == db_aisystem.id).all()
    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_aisystem.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_aisystem.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_aisystem.id).all()
    response_data = {
        "aisystem": db_aisystem,
        "dataset_ids": [x[0] for x in dataset_ids],
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]}
    return response_data



@app.post("/aisystem/", response_model=None, tags=["AISystem"])
async def create_aisystem(aisystem_data: AISystemCreate, database: Session = Depends(get_db)) -> AISystem:

    if aisystem_data.project :
        db_project = database.query(Project).filter(Project.id == aisystem_data.project).first()
        if not db_project:
            raise HTTPException(status_code=400, detail="Project not found")
    if not aisystem_data.dataset or len(aisystem_data.dataset) < 1:
        raise HTTPException(status_code=400, detail="At least 1 Dataset(s) required")
    if aisystem_data.dataset:
        for id in aisystem_data.dataset:
            # Entity already validated before creation
            db_dataset = database.query(Dataset).filter(Dataset.id == id).first()
            if not db_dataset:
                raise HTTPException(status_code=404, detail=f"Dataset with ID {id} not found")
    if aisystem_data.eval:
        for id in aisystem_data.eval:
            # Entity already validated before creation
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == id).first()
            if not db_evaluation:
                raise HTTPException(status_code=404, detail=f"Evaluation with ID {id} not found")

    db_aisystem = AISystem(
        name=aisystem_data.name,        description=aisystem_data.description,        settings=aisystem_data.settings,        version=aisystem_data.version,        licensing=aisystem_data.licensing.value,        source=aisystem_data.source,        data=aisystem_data.data,        project_id=aisystem_data.project        )

    database.add(db_aisystem)
    database.commit()
    database.refresh(db_aisystem)

    if aisystem_data.measure:
        # Validate that all Measure IDs exist
        for measure_id in aisystem_data.measure:
            db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
            if not db_measure:
                raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

        # Update the related entities with the new foreign key
        database.query(Measure).filter(Measure.id.in_(aisystem_data.measure)).update(
            {Measure.measurand_id: db_aisystem.id}, synchronize_session=False
        )
        database.commit()
    if aisystem_data.evalu:
        # Validate that all Evaluation IDs exist
        for evaluation_id in aisystem_data.evalu:
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not db_evaluation:
                raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

        # Update the related entities with the new foreign key
        database.query(Evaluation).filter(Evaluation.id.in_(aisystem_data.evalu)).update(
            {Evaluation.evaluates_id: db_aisystem.id}, synchronize_session=False
        )
        database.commit()

    if aisystem_data.dataset:
        for id in aisystem_data.dataset:
            # Entity already validated before creation
            db_dataset = database.query(Dataset).filter(Dataset.id == id).first()
            # Create the association
            association = aisystem_dataset.insert().values(models=db_aisystem.id, dataset=db_dataset.id)
            database.execute(association)
            database.commit()
    if aisystem_data.eval:
        for id in aisystem_data.eval:
            # Entity already validated before creation
            db_evaluation = database.query(Evaluation).filter(Evaluation.id == id).first()
            # Create the association
            association = evaluation_element.insert().values(ref=db_aisystem.id, eval=db_evaluation.id)
            database.execute(association)
            database.commit()


    dataset_ids = database.query(aisystem_dataset.c.dataset).filter(aisystem_dataset.c.models == db_aisystem.id).all()
    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_aisystem.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_aisystem.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_aisystem.id).all()
    response_data = {
        "aisystem": db_aisystem,
        "dataset_ids": [x[0] for x in dataset_ids],
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]    }
    return response_data


@app.post("/aisystem/bulk/", response_model=None, tags=["AISystem"])
async def bulk_create_aisystem(items: list[AISystemCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple AISystem entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_aisystem = AISystem(
                name=item_data.name,                description=item_data.description,                settings=item_data.settings,                version=item_data.version,                licensing=item_data.licensing.value,                source=item_data.source,                data=item_data.data,                project_id=item_data.project            )
            database.add(db_aisystem)
            database.flush()  # Get ID without committing
            created_items.append(db_aisystem.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} AISystem entities"
    }


@app.delete("/aisystem/bulk/", response_model=None, tags=["AISystem"])
async def bulk_delete_aisystem(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple AISystem entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_aisystem = database.query(AISystem).filter(AISystem.id == item_id).first()
        if db_aisystem:
            database.delete(db_aisystem)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} AISystem entities"
    }

@app.put("/aisystem/{aisystem_id}/", response_model=None, tags=["AISystem"])
async def update_aisystem(aisystem_id: int, aisystem_data: AISystemCreate, database: Session = Depends(get_db)) -> AISystem:
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    setattr(db_aisystem, 'settings', aisystem_data.settings)
    setattr(db_aisystem, 'version', aisystem_data.version)
    setattr(db_aisystem, 'licensing', aisystem_data.licensing.value)
    setattr(db_aisystem, 'source', aisystem_data.source)
    setattr(db_aisystem, 'data', aisystem_data.data)
    if aisystem_data.measure is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Measure).filter(Measure.measurand_id == db_aisystem.id).update(
            {Measure.measurand_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if aisystem_data.measure:
            # Validate that all IDs exist
            for measure_id in aisystem_data.measure:
                db_measure = database.query(Measure).filter(Measure.id == measure_id).first()
                if not db_measure:
                    raise HTTPException(status_code=400, detail=f"Measure with id {measure_id} not found")

            # Update the related entities with the new foreign key
            database.query(Measure).filter(Measure.id.in_(aisystem_data.measure)).update(
                {Measure.measurand_id: db_aisystem.id}, synchronize_session=False
            )
    if aisystem_data.evalu is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Evaluation).filter(Evaluation.evaluates_id == db_aisystem.id).update(
            {Evaluation.evaluates_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if aisystem_data.evalu:
            # Validate that all IDs exist
            for evaluation_id in aisystem_data.evalu:
                db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
                if not db_evaluation:
                    raise HTTPException(status_code=400, detail=f"Evaluation with id {evaluation_id} not found")

            # Update the related entities with the new foreign key
            database.query(Evaluation).filter(Evaluation.id.in_(aisystem_data.evalu)).update(
                {Evaluation.evaluates_id: db_aisystem.id}, synchronize_session=False
            )
    existing_dataset_ids = [assoc.dataset for assoc in database.execute(
        aisystem_dataset.select().where(aisystem_dataset.c.models == db_aisystem.id))]

    datasets_to_remove = set(existing_dataset_ids) - set(aisystem_data.dataset)
    for dataset_id in datasets_to_remove:
        association = aisystem_dataset.delete().where(
            (aisystem_dataset.c.models == db_aisystem.id) & (aisystem_dataset.c.dataset == dataset_id))
        database.execute(association)

    new_dataset_ids = set(aisystem_data.dataset) - set(existing_dataset_ids)
    for dataset_id in new_dataset_ids:
        db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
        if db_dataset is None:
            raise HTTPException(status_code=404, detail=f"Dataset with ID {dataset_id} not found")
        association = aisystem_dataset.insert().values(dataset=db_dataset.id, models=db_aisystem.id)
        database.execute(association)
    existing_evaluation_ids = [assoc.eval for assoc in database.execute(
        evaluation_element.select().where(evaluation_element.c.ref == db_aisystem.id))]

    evaluations_to_remove = set(existing_evaluation_ids) - set(aisystem_data.eval)
    for evaluation_id in evaluations_to_remove:
        association = evaluation_element.delete().where(
            (evaluation_element.c.ref == db_aisystem.id) & (evaluation_element.c.eval == evaluation_id))
        database.execute(association)

    new_evaluation_ids = set(aisystem_data.eval) - set(existing_evaluation_ids)
    for evaluation_id in new_evaluation_ids:
        db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if db_evaluation is None:
            raise HTTPException(status_code=404, detail=f"Evaluation with ID {evaluation_id} not found")
        association = evaluation_element.insert().values(eval=db_evaluation.id, ref=db_aisystem.id)
        database.execute(association)
    database.commit()
    database.refresh(db_aisystem)

    dataset_ids = database.query(aisystem_dataset.c.dataset).filter(aisystem_dataset.c.models == db_aisystem.id).all()
    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == db_aisystem.id).all()
    measure_ids = database.query(Measure.id).filter(Measure.measurand_id == db_aisystem.id).all()
    evalu_ids = database.query(Evaluation.id).filter(Evaluation.evaluates_id == db_aisystem.id).all()
    response_data = {
        "aisystem": db_aisystem,
        "dataset_ids": [x[0] for x in dataset_ids],
        "evaluation_ids": [x[0] for x in evaluation_ids],
        "measure_ids": [x[0] for x in measure_ids],        "evalu_ids": [x[0] for x in evalu_ids]    }
    return response_data


@app.delete("/aisystem/{aisystem_id}/", response_model=None, tags=["AISystem"])
async def delete_aisystem(aisystem_id: int, database: Session = Depends(get_db)):
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")
    database.delete(db_aisystem)
    database.commit()
    return db_aisystem

@app.post("/aisystem/{aisystem_id}/dataset/{dataset_id}/", response_model=None, tags=["AISystem Relationships"])
async def add_dataset_to_aisystem(aisystem_id: int, dataset_id: int, database: Session = Depends(get_db)):
    """Add a Dataset to this AISystem's dataset relationship"""
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    db_dataset = database.query(Dataset).filter(Dataset.id == dataset_id).first()
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Check if relationship already exists
    existing = database.query(aisystem_dataset).filter(
        (aisystem_dataset.c.models == aisystem_id) &
        (aisystem_dataset.c.dataset == dataset_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = aisystem_dataset.insert().values(models=aisystem_id, dataset=dataset_id)
    database.execute(association)
    database.commit()

    return {"message": "Dataset added to dataset successfully"}


@app.delete("/aisystem/{aisystem_id}/dataset/{dataset_id}/", response_model=None, tags=["AISystem Relationships"])
async def remove_dataset_from_aisystem(aisystem_id: int, dataset_id: int, database: Session = Depends(get_db)):
    """Remove a Dataset from this AISystem's dataset relationship"""
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    # Check if relationship exists
    existing = database.query(aisystem_dataset).filter(
        (aisystem_dataset.c.models == aisystem_id) &
        (aisystem_dataset.c.dataset == dataset_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = aisystem_dataset.delete().where(
        (aisystem_dataset.c.models == aisystem_id) &
        (aisystem_dataset.c.dataset == dataset_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Dataset removed from dataset successfully"}


@app.get("/aisystem/{aisystem_id}/dataset/", response_model=None, tags=["AISystem Relationships"])
async def get_dataset_of_aisystem(aisystem_id: int, database: Session = Depends(get_db)):
    """Get all Dataset entities related to this AISystem through dataset"""
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    dataset_ids = database.query(aisystem_dataset.c.dataset).filter(aisystem_dataset.c.models == aisystem_id).all()
    dataset_list = database.query(Dataset).filter(Dataset.id.in_([id[0] for id in dataset_ids])).all()

    return {
        "aisystem_id": aisystem_id,
        "dataset_count": len(dataset_list),
        "dataset": dataset_list
    }

@app.post("/aisystem/{aisystem_id}/eval/{evaluation_id}/", response_model=None, tags=["AISystem Relationships"])
async def add_eval_to_aisystem(aisystem_id: int, evaluation_id: int, database: Session = Depends(get_db)):
    """Add a Evaluation to this AISystem's eval relationship"""
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    db_evaluation = database.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if db_evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Check if relationship already exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.ref == aisystem_id) &
        (evaluation_element.c.eval == evaluation_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = evaluation_element.insert().values(ref=aisystem_id, eval=evaluation_id)
    database.execute(association)
    database.commit()

    return {"message": "Evaluation added to eval successfully"}


@app.delete("/aisystem/{aisystem_id}/eval/{evaluation_id}/", response_model=None, tags=["AISystem Relationships"])
async def remove_eval_from_aisystem(aisystem_id: int, evaluation_id: int, database: Session = Depends(get_db)):
    """Remove a Evaluation from this AISystem's eval relationship"""
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    # Check if relationship exists
    existing = database.query(evaluation_element).filter(
        (evaluation_element.c.ref == aisystem_id) &
        (evaluation_element.c.eval == evaluation_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = evaluation_element.delete().where(
        (evaluation_element.c.ref == aisystem_id) &
        (evaluation_element.c.eval == evaluation_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Evaluation removed from eval successfully"}


@app.get("/aisystem/{aisystem_id}/eval/", response_model=None, tags=["AISystem Relationships"])
async def get_eval_of_aisystem(aisystem_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this AISystem through eval"""
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    evaluation_ids = database.query(evaluation_element.c.eval).filter(evaluation_element.c.ref == aisystem_id).all()
    evaluation_list = database.query(Evaluation).filter(Evaluation.id.in_([id[0] for id in evaluation_ids])).all()

    return {
        "aisystem_id": aisystem_id,
        "eval_count": len(evaluation_list),
        "eval": evaluation_list
    }


@app.get("/aisystem/{aisystem_id}/measure/", response_model=None, tags=["AISystem Relationships"])
async def get_measure_of_aisystem(aisystem_id: int, database: Session = Depends(get_db)):
    """Get all Measure entities related to this AISystem through measure"""
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    measure_list = database.query(Measure).filter(Measure.measurand_id == aisystem_id).all()

    return {
        "aisystem_id": aisystem_id,
        "measure_count": len(measure_list),
        "measure": measure_list
    }

@app.get("/aisystem/{aisystem_id}/evalu/", response_model=None, tags=["AISystem Relationships"])
async def get_evalu_of_aisystem(aisystem_id: int, database: Session = Depends(get_db)):
    """Get all Evaluation entities related to this AISystem through evalu"""
    db_aisystem = database.query(AISystem).filter(AISystem.id == aisystem_id).first()
    if db_aisystem is None:
        raise HTTPException(status_code=404, detail="AISystem not found")

    evalu_list = database.query(Evaluation).filter(Evaluation.evaluates_id == aisystem_id).all()

    return {
        "aisystem_id": aisystem_id,
        "evalu_count": len(evalu_list),
        "evalu": evalu_list
    }







############################################
# Maintaining the server
############################################
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




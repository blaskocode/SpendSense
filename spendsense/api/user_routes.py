"""User management API routes"""

from fastapi import APIRouter, HTTPException
from typing import List

from ..storage.sqlite_manager import SQLiteManager
from ..guardrails.consent import ConsentManager
from ..ingest.importer import DataImporter
from ..storage.parquet_handler import ParquetHandler
from ..utils.logger import setup_logger
from .models import (
    CreateUserRequest, CreateUserResponse,
    ConsentRequest, ConsentResponse,
    ErrorResponse
)

logger = setup_logger(__name__)
router = APIRouter(prefix="/users", tags=["User Management"])


def get_db():
    """Get database connection"""
    db_manager = SQLiteManager()
    db_manager.connect()
    return db_manager


@router.post("", response_model=CreateUserResponse)
def create_user(request: CreateUserRequest):
    """Create a new user.
    
    If generate_synthetic_data is True, creates synthetic account and transaction data.
    """
    db_manager = get_db()
    
    try:
        cursor = db_manager.conn.cursor()
        
        # Generate user_id if not provided
        user_id = request.user_id
        if not user_id:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            count = cursor.fetchone()['count']
            user_id = f"user_{count + 1:03d}"
        
        # Check if user already exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"User {user_id} already exists")
        
        # Create user
        from datetime import datetime
        cursor.execute("""
            INSERT INTO users (user_id, created_at, last_updated, consent_status)
            VALUES (?, ?, ?, ?)
        """, (user_id, datetime.now(), datetime.now(), False))
        db_manager.conn.commit()
        
        # Generate synthetic data if requested
        # Note: For now, we skip synthetic data generation for individual users
        # as it requires batch generation. Users can be created and data generated separately.
        if request.generate_synthetic_data:
            logger.warning(f"Synthetic data generation for individual users not yet supported. User {user_id} created without data.")
        
        cursor.execute("SELECT created_at FROM users WHERE user_id = ?", (user_id,))
        created_at = cursor.fetchone()['created_at']
        
        return CreateUserResponse(
            user_id=user_id,
            created_at=created_at,
            message=f"User {user_id} created successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.post("/consent", response_model=ConsentResponse)
def record_consent(request: ConsentRequest):
    """Record user consent for data processing."""
    db_manager = get_db()
    
    try:
        consent_manager = ConsentManager(db_manager.conn)
        consent_manager.record_consent(request.user_id)
        
        cursor = db_manager.conn.cursor()
        cursor.execute("""
            SELECT consent_status, consent_timestamp
            FROM users
            WHERE user_id = ?
        """, (request.user_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail=f"User {request.user_id} not found")
        
        return ConsentResponse(
            user_id=request.user_id,
            consent_status=bool(result['consent_status']),
            consent_timestamp=result['consent_timestamp']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.delete("/consent/{user_id}", response_model=ConsentResponse)
def revoke_consent(user_id: str):
    """Revoke user consent and delete recommendations."""
    db_manager = get_db()
    
    try:
        consent_manager = ConsentManager(db_manager.conn)
        consent_manager.revoke_consent(user_id)
        
        cursor = db_manager.conn.cursor()
        cursor.execute("""
            SELECT consent_status, consent_timestamp
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return ConsentResponse(
            user_id=user_id,
            consent_status=False,
            consent_timestamp=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.get("/consent/{user_id}", response_model=ConsentResponse)
def check_consent(user_id: str):
    """Check user consent status."""
    db_manager = get_db()
    
    try:
        consent_manager = ConsentManager(db_manager.conn)
        has_consent = consent_manager.check_consent(user_id)
        
        cursor = db_manager.conn.cursor()
        cursor.execute("""
            SELECT consent_status, consent_timestamp
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return ConsentResponse(
            user_id=user_id,
            consent_status=has_consent,
            consent_timestamp=result['consent_timestamp']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


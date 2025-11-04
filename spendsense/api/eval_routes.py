"""Evaluation API routes"""

from fastapi import APIRouter, HTTPException

from ..storage.sqlite_manager import SQLiteManager
from ..eval.scoring import ScoringSystem
from ..eval.satisfaction import SatisfactionMetrics
from ..eval.fairness import FairnessAnalyzer
from ..eval.reporter import EvaluationReporter
from ..utils.logger import setup_logger
from .models import EvaluationMetricsResponse, ErrorResponse

logger = setup_logger(__name__)
router = APIRouter(prefix="/eval", tags=["Evaluation"])


def get_db():
    """Get database connection"""
    db_manager = SQLiteManager()
    db_manager.connect()
    return db_manager


@router.get("/metrics", response_model=EvaluationMetricsResponse)
def get_evaluation_metrics():
    """Get evaluation metrics (scoring, satisfaction, fairness)."""
    db_manager = get_db()
    
    try:
        scoring = ScoringSystem(db_manager.conn)
        satisfaction = SatisfactionMetrics(db_manager.conn)
        fairness = FairnessAnalyzer(db_manager.conn)
        
        # Compute all metrics
        scoring_metrics = scoring.compute_all_scores(latency_sample_size=10)
        satisfaction_metrics = satisfaction.compute_all_satisfaction_metrics()
        fairness_metrics = fairness.compute_all_fairness_metrics()
        
        return EvaluationMetricsResponse(
            scoring=scoring_metrics,
            satisfaction=satisfaction_metrics,
            fairness=fairness_metrics,
            evaluation_date=scoring_metrics['computed_at']
        )
    
    except Exception as e:
        logger.error(f"Error getting evaluation metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.post("/run")
def run_evaluation(latency_sample_size: int = 10):
    """Trigger a full evaluation run and generate reports."""
    db_manager = get_db()
    
    try:
        reporter = EvaluationReporter(db_manager.conn)
        results = reporter.run_full_evaluation(latency_sample_size=latency_sample_size)
        
        return {
            "success": True,
            "message": "Evaluation completed successfully",
            "output_files": results['output_files'],
            "metrics": {
                "scoring": results['scoring'],
                "satisfaction": results['satisfaction'],
                "fairness": results['fairness']
            }
        }
    
    except Exception as e:
        logger.error(f"Error running evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.get("/fairness")
def get_fairness_report():
    """Get fairness analysis report."""
    db_manager = get_db()
    
    try:
        fairness = FairnessAnalyzer(db_manager.conn)
        fairness_metrics = fairness.compute_all_fairness_metrics()
        
        return fairness_metrics
    
    except Exception as e:
        logger.error(f"Error getting fairness report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


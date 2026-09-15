"""
Human-In-The-Loop (HITL) Review Service & Active Learning Candidate Stage.

STRICT PRINCIPLES:
1. Preserve full audit trail: Original prediction, Human correction, Reviewer, Timestamp, Model version.
2. Low-confidence or ambiguous detections (< 0.80) are flagged as REVIEW REQUIRED.
3. Export verified corrections as active learning training candidates.
4. Do NOT automatically retrain production models.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.schemas.review import (
    HumanCorrectionInput,
    ReviewItemRecord,
    ReviewQueueResponse,
    ReviewStatusEnum,
)

# In-memory review database store
REVIEW_RECORDS_STORE: Dict[str, ReviewItemRecord] = {}


class ReviewService:
    """
    Manages human verification workflows, audit logging, and active learning staging.
    """

    @staticmethod
    def initialize_review_queue_from_analysis(
        analysis_id: str,
        regions: List[Dict[str, Any]],
        model_version: str = "1.0.0",
    ) -> List[ReviewItemRecord]:
        """
        Flag low-confidence (<0.80) or ambiguous change regions for human review.
        """
        created_records: List[ReviewItemRecord] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for r in regions:
            props = r.get("properties", r)
            reg_idx = props.get("region_index", 1)
            conf = float(props.get("mean_confidence", props.get("confidence", 0.90)))
            cat = str(props.get("category", "HUMAN")).upper()
            subcat = str(props.get("subcategory", props.get("subtype", "Unknown")))

            # Regions with confidence < 0.80 or category UNKNOWN require review
            if conf < 0.80 or cat == "UNKNOWN":
                rev_id = f"REV-{analysis_id}-{reg_idx}"
                if rev_id not in REVIEW_RECORDS_STORE:
                    record = ReviewItemRecord(
                        review_id=rev_id,
                        analysis_id=analysis_id,
                        region_index=reg_idx,
                        original_category=cat,
                        original_subcategory=subcat,
                        original_confidence=conf,
                        corrected_category=None,
                        corrected_subcategory=None,
                        status=ReviewStatusEnum.PENDING,
                        reviewer_name="Unassigned",
                        notes=f"Flagged for review due to confidence score ({conf * 100:.1f}%)" if conf < 0.80 else "Flagged for review due to ambiguous spectral category",
                        model_version=model_version,
                        is_active_learning_candidate=True,
                        created_at=now_iso,
                        updated_at=now_iso,
                    )
                    REVIEW_RECORDS_STORE[rev_id] = record
                    created_records.append(record)

        return created_records

    @staticmethod
    def submit_reviews(
        analysis_id: str,
        corrections: List[HumanCorrectionInput],
        reviewer_name: str = "GIS Analyst",
        model_version: str = "1.0.0",
    ) -> List[ReviewItemRecord]:
        """
        Record human corrections and approvals with full audit logging.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        updated_records: List[ReviewItemRecord] = []

        for corr in corrections:
            rev_id = f"REV-{analysis_id}-{corr.region_index}"

            if rev_id in REVIEW_RECORDS_STORE:
                existing = REVIEW_RECORDS_STORE[rev_id]
                updated = ReviewItemRecord(
                    review_id=rev_id,
                    analysis_id=analysis_id,
                    region_index=corr.region_index,
                    original_category=existing.original_category,
                    original_subcategory=existing.original_subcategory,
                    original_confidence=existing.original_confidence,
                    corrected_category=corr.corrected_category or existing.corrected_category or existing.original_category,
                    corrected_subcategory=corr.corrected_subcategory or existing.corrected_subcategory or existing.original_subcategory,
                    status=corr.status,
                    reviewer_name=corr.reviewer_name or reviewer_name,
                    notes=corr.notes or existing.notes,
                    model_version=model_version,
                    is_active_learning_candidate=corr.mark_as_training_candidate,
                    created_at=existing.created_at,
                    updated_at=now_iso,
                )
            else:
                updated = ReviewItemRecord(
                    review_id=rev_id,
                    analysis_id=analysis_id,
                    region_index=corr.region_index,
                    original_category="UNKNOWN",
                    original_subcategory="Unknown",
                    original_confidence=0.75,
                    corrected_category=corr.corrected_category or "HUMAN",
                    corrected_subcategory=corr.corrected_subcategory or "Building",
                    status=corr.status,
                    reviewer_name=corr.reviewer_name or reviewer_name,
                    notes=corr.notes,
                    model_version=model_version,
                    is_active_learning_candidate=corr.mark_as_training_candidate,
                    created_at=now_iso,
                    updated_at=now_iso,
                )

            REVIEW_RECORDS_STORE[rev_id] = updated
            updated_records.append(updated)

        return updated_records

    @staticmethod
    def get_review_queue(
        analysis_id: Optional[str] = None,
        status_filter: Optional[ReviewStatusEnum] = None,
    ) -> ReviewQueueResponse:
        """
        Get list of review queue items with status counts.
        """
        items = list(REVIEW_RECORDS_STORE.values())

        if analysis_id:
            items = [it for it in items if it.analysis_id == analysis_id]

        if status_filter:
            items = [it for it in items if it.status == status_filter]

        pending = sum(1 for it in items if it.status == ReviewStatusEnum.PENDING)
        corrected = sum(1 for it in items if it.status == ReviewStatusEnum.CORRECTED)
        approved = sum(1 for it in items if it.status == ReviewStatusEnum.APPROVED)

        return ReviewQueueResponse(
            total_in_queue=len(items),
            pending_count=pending,
            corrected_count=corrected,
            approved_count=approved,
            items=items,
        )

    @staticmethod
    def export_active_learning_dataset(export_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Export approved and corrected samples into an active learning training candidate dataset.
        Enforces rule: Does NOT automatically retrain production models.
        """
        target_dir = Path(export_dir or "/tmp/active_learning_candidates")
        target_dir.mkdir(parents=True, exist_ok=True)

        candidates = [
            it.model_dump()
            for it in REVIEW_RECORDS_STORE.values()
            if it.is_active_learning_candidate and it.status in [ReviewStatusEnum.APPROVED, ReviewStatusEnum.CORRECTED]
        ]

        export_file = target_dir / f"active_learning_staged_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, "w") as f:
            json.dump({
                "disclaimer": "Active learning candidates staged. Production models are NOT automatically retrained without explicit validation.",
                "candidate_count": len(candidates),
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "samples": candidates,
            }, f, indent=2)

        return {
            "status": "exported",
            "candidate_count": len(candidates),
            "export_path": str(export_file),
            "message": "Active learning candidates staged. Production models are NOT automatically retrained without explicit verification.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

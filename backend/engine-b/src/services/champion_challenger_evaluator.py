"""
InfinityAI.Pro — Shadow Champion-vs-Challenger Canary Evaluator
===============================================================
Engine B | Production Grade | Version: 3.1.0

Evaluates newly retrained candidate models (Challengers) against active production
models (Champions) in parallel shadow mode across a robust 500-tick canary evaluation window.
Requires a minimum of 200 out-of-sample ticks before triggering autonomous promotion
to eliminate lookahead and small-sample data leakage risks.
"""

import os
import math
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np

try:
    from google.cloud import firestore
except Exception:
    firestore = None

logger = logging.getLogger("InfinityAI.ChampionChallenger")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "project-841b7f97-5ee3-4fbe-920")
METADATA_COLLECTION = "model_metadata"
CHAMPION_DOC_ID = "champion_status"

MIN_OUT_OF_SAMPLE_TICKS_REQUIRED = 200

class ChampionChallengerEvaluator:
    """Shadow Canary Evaluation & Zero-Downtime Model Promotion Rig"""

    def __init__(
        self,
        canary_window_size: int = 500,
        promotion_threshold_pct: float = 3.0,
        min_required_ticks: int = MIN_OUT_OF_SAMPLE_TICKS_REQUIRED,
        project_id: str = PROJECT_ID
    ):
        self.canary_window_size = canary_window_size
        self.promotion_threshold_pct = promotion_threshold_pct
        self.min_required_ticks = min_required_ticks
        self.project_id = project_id

        self.champion_name: str = "TriModel_Ensemble_v2.8"
        self.challenger_name: str = "TriModel_Ensemble_v3.0_Canary"

        self.champion_predictions: List[float] = []
        self.challenger_predictions: List[float] = []
        self.actual_outcomes: List[int] = []
        self.db = None

        if firestore:
            try:
                self.db = firestore.Client(project=self.project_id)
                self._load_status_from_firestore()
            except Exception as e:
                logger.debug(f"Firestore champion-challenger init notice: {e}")

    def _load_status_from_firestore(self) -> None:
        """Loads persistent champion status"""
        if not self.db:
            return
        try:
            doc = self.db.collection(METADATA_COLLECTION).document(CHAMPION_DOC_ID).get()
            if doc.exists:
                data = doc.to_dict()
                self.champion_name = data.get("champion_name", self.champion_name)
                self.challenger_name = data.get("challenger_name", self.challenger_name)
        except Exception as e:
            logger.debug(f"Error loading champion status: {e}")

    def record_canary_tick(
        self,
        champion_prob: float,
        challenger_prob: float,
        actual_outcome: int
    ) -> Dict[str, Any]:
        """
        Records a tick prediction from both Champion and Challenger.
        Applies strict probabilistic clipping to eliminate raw certainty skew.
        """
        c_prob = float(np.clip(champion_prob, 0.01, 0.99))
        ch_prob = float(np.clip(challenger_prob, 0.01, 0.99))
        act_out = int(actual_outcome)

        self.champion_predictions.append(c_prob)
        self.challenger_predictions.append(ch_prob)
        self.actual_outcomes.append(act_out)

        if len(self.actual_outcomes) > self.canary_window_size:
            self.champion_predictions.pop(0)
            self.challenger_predictions.pop(0)
            self.actual_outcomes.pop(0)

        # Compute Out-of-Sample Metrics
        champ_preds = np.array(self.champion_predictions)
        chall_preds = np.array(self.challenger_predictions)
        acts = np.array(self.actual_outcomes)

        champ_brier = float(np.mean((champ_preds - acts) ** 2))
        chall_brier = float(np.mean((chall_preds - acts) ** 2))

        # Relative improvement: (Champ_Loss - Chall_Loss) / Champ_Loss * 100
        relative_improvement_pct = 0.0
        if champ_brier > 0:
            relative_improvement_pct = float((champ_brier - chall_brier) / champ_brier * 100.0)

        evaluated_count = len(self.actual_outcomes)
        promoted = False

        # Strictly require min_required_ticks (>= 200) to prevent small-sample canary traps
        if evaluated_count >= self.min_required_ticks and relative_improvement_pct >= self.promotion_threshold_pct:
            promoted = True
            logger.info(f"🏆 Challenger '{self.challenger_name}' outperformed Champion by {relative_improvement_pct:.2f}% across {evaluated_count} ticks! Promoting to Champion.")
            self.champion_name = self.challenger_name
            self.challenger_name = f"TriModel_Ensemble_v{float(self.champion_name.split('_v')[-1].split('_')[0]) + 0.1:.1f}_Canary"
            self._persist_promotion(relative_improvement_pct, champ_brier, chall_brier, evaluated_count)

        return {
            "canary_ticks_evaluated": evaluated_count,
            "min_ticks_required_for_promotion": self.min_required_ticks,
            "canary_window_size": self.canary_window_size,
            "champion_name": self.champion_name,
            "challenger_name": self.challenger_name,
            "champion_brier_loss": round(champ_brier, 4),
            "challenger_brier_loss": round(chall_brier, 4),
            "relative_improvement_pct": round(relative_improvement_pct, 2),
            "promotion_triggered": promoted
        }

    def _persist_promotion(self, improvement_pct: float, old_brier: float, new_brier: float, sample_size: int) -> None:
        """Persists model promotion event to Firestore"""
        if not self.db:
            return
        try:
            payload = {
                "champion_name": self.champion_name,
                "challenger_name": self.challenger_name,
                "last_promotion_timestamp": datetime.now(timezone.utc).isoformat(),
                "relative_improvement_pct": round(improvement_pct, 2),
                "previous_champion_brier": round(old_brier, 4),
                "new_champion_brier": round(new_brier, 4),
                "out_of_sample_ticks_evaluated": sample_size
            }
            self.db.collection(METADATA_COLLECTION).document(CHAMPION_DOC_ID).set(payload)
        except Exception as e:
            logger.warning(f"Error persisting model promotion: {e}")

CHAMPION_CHALLENGER = ChampionChallengerEvaluator()

import logging

from repositories import case_repository

logger = logging.getLogger(__name__)


def find_similar_cases(
    evidence_package: dict,
    violation_type: str,
    limit: int = 5,
) -> list[dict]:
    resolved_cases, _ = case_repository.get_cases_by_status("resolved", limit=200)

    candidates = [c for c in resolved_cases if c.get("violation_type") == violation_type]

    if not candidates:
        logger.info(
            "No resolved precedent cases found",
            extra={"violation_type": violation_type},
        )
        return []

    scored = []
    for case in candidates:
        similarity = _compute_similarity(evidence_package, case)
        scored.append({
            "case_id": case["case_id"],
            "violation_type": case.get("violation_type", "unknown"),
            "outcome": case.get("enforcement_action", "unknown"),
            "similarity_score": similarity,
            "resolved_at": case.get("resolved_at"),
        })

    scored.sort(key=lambda x: x["similarity_score"], reverse=True)

    results = scored[:limit]
    logger.info(
        "Precedent cases matched",
        extra={
            "violation_type": violation_type,
            "candidates_evaluated": len(candidates),
            "results_returned": len(results),
        },
    )
    return results


def _compute_similarity(evidence_package: dict, resolved_case: dict) -> float:
    score = 0.0

    evidence_trigger = evidence_package.get("trigger_source")
    case_trigger = resolved_case.get("trigger_source")
    if evidence_trigger and case_trigger and evidence_trigger == case_trigger:
        score += 0.5

    case_confidence = resolved_case.get("confidence_score", 0)
    evidence_confidence = evidence_package.get("confidence_score", 0)
    if case_confidence and evidence_confidence:
        try:
            conf_a = float(case_confidence)
            conf_b = float(evidence_confidence)
            diff = abs(conf_a - conf_b)
            score += max(0.0, 0.5 * (1.0 - diff))
        except (ValueError, TypeError):
            pass

    return round(min(score, 1.0), 4)

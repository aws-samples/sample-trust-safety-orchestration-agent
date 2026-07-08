import logging

from repositories import reviewer_repository

logger = logging.getLogger(__name__)


def track_exposure(reviewer_id: str, case_id: str, content_severity: str) -> dict:
    """Track a reviewer's exposure to case content.

    Increments the cases reviewed count. If severity is 'high' or 'critical',
    also increments the harmful exposure count.

    Returns a summary of the exposure tracking action.
    """
    reviewer_repository.increment_cases_reviewed(reviewer_id)

    is_harmful = content_severity in ("high", "critical")
    if is_harmful:
        reviewer_repository.increment_harmful_exposure(reviewer_id)

    logger.info(
        "Reviewer exposure tracked",
        extra={
            "reviewer_id": reviewer_id,
            "case_id": case_id,
            "content_severity": content_severity,
            "harmful_exposure_incremented": is_harmful,
        },
    )

    return {
        "reviewer_id": reviewer_id,
        "case_id": case_id,
        "content_severity": content_severity,
        "harmful_exposure_incremented": is_harmful,
    }


def check_exposure_threshold(reviewer_id: str, daily_limit: int = 20) -> dict:
    """Check if a reviewer has reached their daily exposure threshold and should take a break.

    Returns a dict indicating whether the threshold has been reached and current exposure data.
    """
    state = reviewer_repository.get_reviewer_state(reviewer_id)

    if state is None:
        logger.info(
            "No reviewer state found, threshold not reached",
            extra={"reviewer_id": reviewer_id},
        )
        return {
            "reviewer_id": reviewer_id,
            "threshold_reached": False,
            "cases_reviewed_today": 0,
            "harmful_exposure_today": 0,
            "daily_limit": daily_limit,
            "should_take_break": False,
        }

    cases_reviewed = int(state.get("cases_reviewed", 0))
    harmful_exposure = int(state.get("harmful_exposure_count", 0))

    threshold_reached = harmful_exposure >= daily_limit
    # Also suggest a break if total cases reviewed is very high, even if not all harmful
    should_take_break = threshold_reached or cases_reviewed >= (daily_limit * 3)

    if threshold_reached:
        logger.warning(
            "Reviewer exposure threshold reached",
            extra={
                "reviewer_id": reviewer_id,
                "harmful_exposure": harmful_exposure,
                "daily_limit": daily_limit,
            },
        )
        # Record that we prompted the reviewer about wellness
        reviewer_repository.record_wellness_prompt(reviewer_id)

    return {
        "reviewer_id": reviewer_id,
        "threshold_reached": threshold_reached,
        "cases_reviewed_today": cases_reviewed,
        "harmful_exposure_today": harmful_exposure,
        "daily_limit": daily_limit,
        "should_take_break": should_take_break,
    }


def get_exposure_metrics(reviewer_id: str, period_days: int = 7) -> dict:
    """Get exposure metrics for a reviewer over the specified period.

    Delegates to reviewer_repository.get_exposure_metrics.
    """
    metrics = reviewer_repository.get_exposure_metrics(reviewer_id, days=period_days)

    logger.info(
        "Exposure metrics retrieved",
        extra={"reviewer_id": reviewer_id, "period_days": period_days},
    )

    return metrics


def distribute_critical_case(case_id: str, available_reviewers: list[str]) -> dict:
    """Distribute a critical case to the reviewer with the lowest harmful exposure today.

    Examines each available reviewer's current state and picks the one with the
    fewest harmful content exposures for the day, to spread the load evenly.

    Returns a dict with the selected reviewer ID and their current exposure.
    """
    if not available_reviewers:
        logger.warning(
            "No available reviewers for critical case distribution",
            extra={"case_id": case_id},
        )
        return {
            "case_id": case_id,
            "assigned_reviewer_id": None,
            "reason": "no_available_reviewers",
        }

    best_reviewer = None
    lowest_harmful_exposure = float("inf")

    for reviewer_id in available_reviewers:
        state = reviewer_repository.get_reviewer_state(reviewer_id)
        harmful_exposure = int(state.get("harmful_exposure_count", 0)) if state else 0

        if harmful_exposure < lowest_harmful_exposure:
            lowest_harmful_exposure = harmful_exposure
            best_reviewer = reviewer_id

    logger.info(
        "Critical case distributed to reviewer with lowest harmful exposure",
        extra={
            "case_id": case_id,
            "assigned_reviewer_id": best_reviewer,
            "harmful_exposure_today": lowest_harmful_exposure,
            "candidates_evaluated": len(available_reviewers),
        },
    )

    return {
        "case_id": case_id,
        "assigned_reviewer_id": best_reviewer,
        "harmful_exposure_today": lowest_harmful_exposure,
        "candidates_evaluated": len(available_reviewers),
    }

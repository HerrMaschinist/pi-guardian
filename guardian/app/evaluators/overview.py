from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from guardian.app.collectors.router_collector import GuardianRouterCollectorState
from guardian.app.core.domain import GuardianSeverity, GuardianSignalSource
from guardian.app.evaluators.common import GuardianEvaluationReason
from guardian.app.evaluators.router_evaluator import GuardianRouterEvaluation
from guardian.app.storage.models import GuardianPersistenceReceipt
from guardian.app.system.evaluator import GuardianSystemEvaluation
from guardian.app.system.models import GuardianSystemCollectorState
from guardian.app.policy.models import GuardianPolicyDecision


class GuardianOverviewEvaluation(BaseModel):
    status: GuardianSeverity
    summary: str
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reasons: list[GuardianEvaluationReason] = Field(default_factory=list)
    router: GuardianRouterEvaluation
    system: GuardianSystemEvaluation


class GuardianStatusResponse(BaseModel):
    status: GuardianSeverity
    component: str = "guardian"
    version: str = "0.1.0"
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    router: GuardianRouterCollectorState
    router_evaluation: GuardianRouterEvaluation
    system: GuardianSystemCollectorState
    system_evaluation: GuardianSystemEvaluation
    evaluation: GuardianOverviewEvaluation
    persistence: GuardianPersistenceReceipt | None = None
    policy: GuardianPolicyDecision | None = None


class GuardianOverviewEvaluator:
    """Combines router and system evaluations into a single Guardian view."""

    def evaluate(
        self,
        router_evaluation: GuardianRouterEvaluation,
        system_evaluation: GuardianSystemEvaluation,
    ) -> GuardianOverviewEvaluation:
        reasons: list[GuardianEvaluationReason] = []

        status = GuardianSeverity.OK
        summary = "Guardian is healthy."

        if router_evaluation.status == GuardianSeverity.CRITICAL or system_evaluation.status == GuardianSeverity.CRITICAL:
            status = GuardianSeverity.CRITICAL
            summary = "Guardian has a critical condition."
        elif router_evaluation.status == GuardianSeverity.WARN or system_evaluation.status == GuardianSeverity.WARN:
            status = GuardianSeverity.WARN
            summary = "Guardian needs attention."

        if router_evaluation.status != GuardianSeverity.OK:
            reasons.append(
                GuardianEvaluationReason(
                    code=f"router_{router_evaluation.status.value}",
                    summary=f"Router evaluation returned {router_evaluation.status.value}.",
                    severity=router_evaluation.status,
                    source=GuardianSignalSource.ROUTER,
                    detail=router_evaluation.summary,
                    evidence={
                        "reason_codes": [reason.code for reason in router_evaluation.reasons],
                        "reason_count": len(router_evaluation.reasons),
                    },
                )
            )

        if system_evaluation.status != GuardianSeverity.OK:
            reasons.append(
                GuardianEvaluationReason(
                    code=f"system_{system_evaluation.status.value}",
                    summary=f"System evaluation returned {system_evaluation.status.value}.",
                    severity=system_evaluation.status,
                    source=GuardianSignalSource.SYSTEM,
                    detail=system_evaluation.summary,
                    evidence={
                        "reason_codes": [reason.code for reason in system_evaluation.reasons],
                        "reason_count": len(system_evaluation.reasons),
                    },
                )
            )

        if not reasons:
            reasons.append(
                GuardianEvaluationReason(
                    code="guardian_overall_ok",
                    summary="Router and system evaluations are healthy.",
                    severity=GuardianSeverity.OK,
                    source=GuardianSignalSource.EXTERNAL,
                    evidence={
                        "router_status": router_evaluation.status,
                        "system_status": system_evaluation.status,
                    },
                )
            )

        return GuardianOverviewEvaluation(
            status=status,
            summary=summary,
            reasons=reasons,
            router=router_evaluation,
            system=system_evaluation,
        )

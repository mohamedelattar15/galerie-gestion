"""Single source of truth for Feature Relevance Estimation settings.

Every tunable value of the G13 method lives here so the formula, the API
workflow and the offline evaluation can never drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass

# Equation (4) of the reference paper: w_i = 1 / (epsilon + sigma_rel_i).
DEFAULT_EPSILON = 0.0001

# Project guard rail: a standard deviation needs at least two samples.
DEFAULT_MINIMUM_RELEVANT = 2

# Interface default: how many results are displayed and judged.
DEFAULT_TOP_K = 10


@dataclass(frozen=True)
class FreSettings:
    """Parameters of one FRE experiment."""

    epsilon: float = DEFAULT_EPSILON
    minimum_relevant: int = DEFAULT_MINIMUM_RELEVANT
    top_k: int = DEFAULT_TOP_K
    feedback_pool: int | None = None
    feedback_count: int = 5

    def resolved_feedback_pool(self) -> int:
        """Return the number of judged results, defaulting to the visible ones.

        The interface only lets the user judge the results it displays, so the
        offline simulation must inspect the same window. Passing a larger pool
        simulates an oracle and must be reported explicitly.
        """
        return self.top_k if self.feedback_pool is None else self.feedback_pool

    def validate(self, image_count: int) -> None:
        if not 1 <= self.top_k < image_count:
            raise ValueError(f"top_k doit être compris entre 1 et {image_count - 1}.")
        pool = self.resolved_feedback_pool()
        if not self.top_k <= pool < image_count:
            raise ValueError("feedback_pool doit être entre top_k et le nombre d'images moins un.")
        if not 2 <= self.feedback_count <= pool:
            raise ValueError("feedback_count doit être entre 2 et feedback_pool.")
        if not self.epsilon > 0:
            raise ValueError("epsilon doit être strictement positif.")
        if self.minimum_relevant < 2:
            raise ValueError("minimum_relevant doit être supérieur ou égal à 2.")

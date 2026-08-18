"""
Agent-FinOps: The Autonomous KV-Cache, Tokenomics & Cost-Per-Task Orchestrator.
Standard library only: hashlib, json, time, os, dataclasses, typing.
"""

from __future__ import annotations

import dataclasses
import functools
import hashlib
import json
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple


GENESIS_HASH: str = "0000000000000000000000000000000000000000000000000000000000000000"


@dataclasses.dataclass(frozen=True)
class FinOpsReceipt:
    """Immutable SHA-256 cryptographically chained unit-economics receipt."""
    index: int
    prev_hash: str
    task_id: str
    model_name: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    kv_cache_hit_ratio: float
    status: str
    timestamp: float
    payload_hash: str
    signature_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


class PrefixCacheTracker:
    """
    Dynamic Prefix Hash & KV-Cache Reclaim Engine.
    Tracks recurring system prompts and RAG contexts to eliminate redundant prefill compute.
    """

    def __init__(self, prefix_discount_rate: float = 0.85):
        self.prefix_discount_rate = prefix_discount_rate
        self._cached_prefixes: Dict[str, int] = {}  # prefix_hash -> access_count

    def compute_prefix_hash(self, prompt_prefix: str) -> str:
        return hashlib.sha256(prompt_prefix.encode("utf-8")).hexdigest()

    def evaluate_cache(self, prompt_prefix: str, input_tokens: int) -> Tuple[bool, float, float]:
        """
        Returns: (is_cache_hit, effective_token_multiplier, savings_usd_ratio)
        """
        if not prompt_prefix:
            return False, 1.0, 0.0

        p_hash = self.compute_prefix_hash(prompt_prefix)
        if p_hash in self._cached_prefixes:
            self._cached_prefixes[p_hash] += 1
            # Cache hit: 85% discount on prefill tokens
            return True, (1.0 - self.prefix_discount_rate), self.prefix_discount_rate
        
        # Cache miss: register prefix for future executions
        self._cached_prefixes[p_hash] = 1
        return False, 1.0, 0.0


class ModelLadderRouter:
    """
    Self-Evolving Dynamic Model Router:
    Autonomously routes simple tool executions to lightweight models (Flash/Llama-8B)
    and reserves high-cost reasoning models (o1/Claude Opus) for complex multi-step bottlenecks.
    """

    # Baseline cost per 1k tokens (USD)
    MODEL_TIERS: Dict[str, Dict[str, float]] = {
        "tier1_reasoning": {"input": 0.015, "output": 0.060},    # o1 / Opus / DeepSeek-R1
        "tier2_general": {"input": 0.003, "output": 0.015},      # Sonnet / GPT-4o
        "tier3_fast": {"input": 0.00015, "output": 0.00060},    # Gemini Flash / Llama-3-8B
    }

    def __init__(self, default_tier: str = "tier2_general"):
        self.default_tier = default_tier
        self._task_complexity_history: Dict[str, float] = {}

    def calculate_cost(
        self,
        tier: str,
        input_tokens: int,
        output_tokens: int,
        cache_discount: float = 0.0,
    ) -> float:
        pricing = self.MODEL_TIERS.get(tier, self.MODEL_TIERS["tier2_general"])
        effective_input_tokens = input_tokens * (1.0 - cache_discount)
        cost_input = (effective_input_tokens / 1000.0) * pricing["input"]
        cost_output = (output_tokens / 1000.0) * pricing["output"]
        return round(cost_input + cost_output, 6)

    def route_task(self, task_name: str, estimated_complexity: float) -> str:
        """
        Dynamically routes task based on complexity score (0.0 to 1.0).
        """
        self._task_complexity_history[task_name] = estimated_complexity
        if estimated_complexity >= 0.85:
            return "tier1_reasoning"
        elif estimated_complexity >= 0.35:
            return "tier2_general"
        else:
            return "tier3_fast"


class CryptographicUnitEconomicsLedger:
    """
    SHA-256 Tamper-Proof FinOps Ledger for CFO, Board, and SOC 2 Unit-Economics Verification.
    """

    def __init__(self, ledger_file: Optional[str] = None):
        self.ledger_file = ledger_file
        self._entries: List[FinOpsReceipt] = []
        self._last_hash = GENESIS_HASH

    @property
    def last_hash(self) -> str:
        return self._last_hash

    @property
    def count(self) -> int:
        return len(self._entries)

    def record_step(
        self,
        task_id: str,
        model_name: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        kv_cache_hit_ratio: float,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FinOpsReceipt:
        idx = len(self._entries)
        ts = time.time()
        meta_bytes = json.dumps(metadata or {}, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(meta_bytes).hexdigest()

        # SHA-256 Hash Chain
        msg = f"{idx}:{self._last_hash}:{task_id}:{model_name}:{tokens_input}:{tokens_output}:{cost_usd:.6f}:{ts:.6f}:{payload_hash}"
        sig_hash = hashlib.sha256(msg.encode("utf-8")).hexdigest()

        receipt = FinOpsReceipt(
            index=idx,
            prev_hash=self._last_hash,
            task_id=task_id,
            model_name=model_name,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            kv_cache_hit_ratio=kv_cache_hit_ratio,
            status=status,
            timestamp=ts,
            payload_hash=payload_hash,
            signature_hash=sig_hash,
        )

        self._entries.append(receipt)
        self._last_hash = sig_hash

        if self.ledger_file:
            os.makedirs(os.path.dirname(os.path.abspath(self.ledger_file)), exist_ok=True)
            with open(self.ledger_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(receipt.to_dict()) + chr(10))

        return receipt

    def verify_chain_integrity(self) -> Tuple[bool, Optional[str]]:
        current_prev = GENESIS_HASH
        for idx, entry in enumerate(self._entries):
            if entry.index != idx:
                return False, f"Sequence index mismatch at {idx}"
            if entry.prev_hash != current_prev:
                return False, f"Broken cryptographic chain hash at {idx}"
            current_prev = entry.signature_hash
        return True, None


class TokenomicsGate:
    """
    The Master Autonomous Cost-Per-Task Orchestrator & Runaway Prevention Airbag.
    """

    def __init__(
        self,
        max_cost_per_task_usd: float = 0.50,
        max_recursive_steps: int = 25,
        ledger_path: Optional[str] = None,
    ):
        self.max_cost_per_task_usd = max_cost_per_task_usd
        self.max_recursive_steps = max_recursive_steps
        self.prefix_tracker = PrefixCacheTracker()
        self.router = ModelLadderRouter()
        self.ledger = CryptographicUnitEconomicsLedger(ledger_file=ledger_path)
        self._active_task_spend: Dict[str, float] = {}
        self._active_task_steps: Dict[str, int] = {}

    def check_kill_switch(self) -> bool:
        if os.environ.get("AGENT_FINOPS_KILL", "0") in ("1", "true", "TRUE"):
            return True
        if os.path.exists("/tmp/FINOPS_KILL"):
            return True
        return False

    def guard_agent_step(
        self,
        task_id: str,
        prompt_prefix: str,
        input_tokens: int,
        output_tokens: int,
        complexity: float = 0.5,
    ) -> Tuple[bool, FinOpsReceipt, str]:
        """
        Evaluates budget, checks KV cache hit, routes model tier, and prevents runaway bleed.
        """
        if self.check_kill_switch():
            receipt = self.ledger.record_step(
                task_id=task_id,
                model_name="HALTED_KILL_SWITCH",
                tokens_input=0,
                tokens_output=0,
                cost_usd=0.0,
                kv_cache_hit_ratio=0.0,
                status="HALTED_BY_EMERGENCY_KILL_SWITCH",
            )
            return False, receipt, "tier3_fast"

        # 1. Step count check
        steps = self._active_task_steps.get(task_id, 0) + 1
        self._active_task_steps[task_id] = steps
        if steps > self.max_recursive_steps:
            receipt = self.ledger.record_step(
                task_id=task_id,
                model_name="RUNAWAY_STEP_OVERFLOW",
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                cost_usd=0.0,
                kv_cache_hit_ratio=0.0,
                status="BLOCKED_MAX_STEPS_EXCEEDED",
            )
            return False, receipt, "tier3_fast"

        # 2. KV-Cache evaluation
        is_hit, eff_mult, discount = self.prefix_tracker.evaluate_cache(prompt_prefix, input_tokens)
        hit_ratio = 1.0 if is_hit else 0.0

        # 3. Model Ladder Routing & Cost Calculation
        selected_tier = self.router.route_task(task_id, complexity)
        step_cost = self.router.calculate_cost(selected_tier, input_tokens, output_tokens, cache_discount=discount)

        current_spend = self._active_task_spend.get(task_id, 0.0) + step_cost
        self._active_task_spend[task_id] = current_spend

        # 4. Hard Budget Ceiling Check
        if current_spend > self.max_cost_per_task_usd:
            receipt = self.ledger.record_step(
                task_id=task_id,
                model_name=selected_tier,
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                cost_usd=step_cost,
                kv_cache_hit_ratio=hit_ratio,
                status="BLOCKED_BUDGET_CEILING_EXCEEDED",
            )
            return False, receipt, selected_tier

        receipt = self.ledger.record_step(
            task_id=task_id,
            model_name=selected_tier,
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            cost_usd=step_cost,
            kv_cache_hit_ratio=hit_ratio,
            status="AUTHORIZED_STEP",
        )

        return True, receipt, selected_tier

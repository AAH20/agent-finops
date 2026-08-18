import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agentfinops.core import TokenomicsGate, PrefixCacheTracker, GENESIS_HASH


class TestAgentFinOps(unittest.TestCase):
    def setUp(self):
        self.gate = TokenomicsGate(max_cost_per_task_usd=0.25, max_recursive_steps=10)

    def test_kv_cache_prefix_savings(self):
        tracker = PrefixCacheTracker(prefix_discount_rate=0.85)
        prefix = 'SYSTEM: You are a secure Tier-1 enterprise agent with 50 tools.'

        # 1st execution: Cache miss
        hit1, mult1, disc1 = tracker.evaluate_cache(prefix, 2000)
        self.assertFalse(hit1)
        self.assertEqual(disc1, 0.0)

        # 2nd execution: Cache hit (85% savings)
        hit2, mult2, disc2 = tracker.evaluate_cache(prefix, 2000)
        self.assertTrue(hit2)
        self.assertEqual(disc2, 0.85)

    def test_model_ladder_and_cryptographic_ledger(self):
        # Step 1: simple subagent tool call (routed to tier3_fast)
        allowed, receipt, tier = self.gate.guard_agent_step(
            task_id='task_support_101',
            prompt_prefix='SYSTEM: Support agent v1',
            input_tokens=1500,
            output_tokens=300,
            complexity=0.20,
        )
        self.assertTrue(allowed)
        self.assertEqual(tier, 'tier3_fast')
        self.assertEqual(receipt.status, 'AUTHORIZED_STEP')
        self.assertNotEqual(receipt.signature_hash, GENESIS_HASH)

        # Step 2: verify cryptographic chain integrity
        is_valid, err = self.gate.ledger.verify_chain_integrity()
        self.assertTrue(is_valid, f'Ledger verification failed: {err}')

    def test_runaway_budget_ceiling_prevention(self):
        # Trigger heavy expensive calls that breach /bin/zsh.25 budget ceiling
        for i in range(5):
            allowed, receipt, _ = self.gate.guard_agent_step(
                task_id='task_runaway_loop',
                prompt_prefix=f'SYSTEM: Heavy complex run {i}',
                input_tokens=10000,
                output_tokens=4000,
                complexity=0.95,  # tier1_reasoning (/bin/zsh.015/1k in, /bin/zsh.060/1k out) -> ~/bin/zsh.39/call
            )
            if not allowed:
                self.assertEqual(receipt.status, 'BLOCKED_BUDGET_CEILING_EXCEEDED')
                break

        self.assertFalse(allowed)


if __name__ == '__main__':
    unittest.main()

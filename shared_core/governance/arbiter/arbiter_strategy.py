# shared_core/governance/arbiter/arbiter_strategy.py

from shared_core.governance.parliament.parliament_schema import Decision

class ArbiterStrategy:
    """
    Arbiter = 不確定性處理者
    只在以下情況介入：
    - 投票接近門檻
    - 低信心或高風險
    """

    def arbitrate(self, votes, context) -> Decision:
        raise NotImplementedError


# shared_core/governance/chair/chair_strategy.py

from typing import Optional
from shared_core.governance.parliament.parliament_schema import Decision

class ChairStrategy:
    """
    Chair = 治理程序守門人（不是決策者）
    職責：
    - 阻擋制度違規
    - 延後不成熟提案
    - 放行進入議會
    """

    def review(self, proposal, context) -> Optional[Decision]:
        """
        return:
          - None      → 放行，進入 Parliament 投票
          - Decision  → 直接治理裁決（rejected / deferred）
        """
        raise NotImplementedError

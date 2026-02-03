from shared_core.perception_core.pipeline_core import PerceptionPipelineCore
from shared_core.pb_lang.pb_event_validator import PBEventValidator
from shared_core.perception_core.perception_gateway import PerceptionGateway
from trading_core.perception.market_adapter import MarketKlineAdapter


def build_market_perception_gateway(mode="realtime"):
    """
    建立市場感知層入口（Singleton 概念）
    """
    # === 關鍵一：strict 規則隨 mode 切換 ===
    strict = mode == "realtime"
    validator = PBEventValidator(strict=True)
    core = PerceptionPipelineCore(validator=validator)

    gateway = PerceptionGateway(
        core=core,
        validator=validator,
        strict=True,
    )

    adapter = MarketKlineAdapter(
        mode=mode,
        validator=validator,
    )

    gateway.register_adapter("market.kline", adapter)

    return gateway

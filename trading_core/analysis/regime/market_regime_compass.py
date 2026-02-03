import pandas as pd

from trading_core.analysis.regime.enums import (
    MacroTrend,
    DistributionStage,
    CapitalPosture,
)


class MarketRegimeCompass:
    """
    World State Classifier (Batch / Offline)

    - 不預測價格
    - 不產生交易訊號
    - 僅描述市場結構狀態
    """

    def __init__(
        self,
        df_15m: pd.DataFrame,
        df_1h: pd.DataFrame,
        df_4h: pd.DataFrame,
        explain: bool = False
    ):
        self.df_15m = df_15m
        self.df_1h = df_1h
        self.df_4h = df_4h
        self.explain = explain

    # =========================
    # Public API
    # =========================
    def classify(self) -> dict:
        macro_trend = self._classify_macro_trend()
        distribution = self._classify_distribution_stage()
        posture = self._classify_capital_posture(
            macro_trend, distribution
        )

        return {
            "macro_trend": macro_trend,
            "distribution_stage": distribution,
            "capital_posture": posture,
        }

    # =========================
    # Internal classifiers
    # =========================
    def _classify_macro_trend(self) -> MacroTrend:
        """
        Macro trend classifier (4h timeframe)
        使用一段時間的結構一致性，而不是最後一根 K
        """
        df = self.df_4h

        if df is None or df.empty:
            if self.explain:
                print("[MacroTrend] df_4h empty → UNKNOWN")
            return MacroTrend.UNKNOWN

        required = {"close", "ema_50"}
        if not required.issubset(df.columns):
            if self.explain:
                print(
                    f"[MacroTrend] missing columns: "
                    f"{required - set(df.columns)} → UNKNOWN"
                )
            return MacroTrend.UNKNOWN

        LOOKBACK = 20          # 可調，但先不要動
        REQUIRED_RATIO = 0.6   # 結構存活門檻

        if len(df) < LOOKBACK:
            if self.explain:
                print(
                    f"[MacroTrend] insufficient bars "
                    f"({len(df)} < {LOOKBACK}) → UNKNOWN"
                )
            return MacroTrend.UNKNOWN

        window = df.iloc[-LOOKBACK:]

        valid = window.dropna(subset=["close", "ema_50"])
        if valid.empty:
            if self.explain:
                print("[MacroTrend] all NaN in window → UNKNOWN")
            return MacroTrend.UNKNOWN

        above_ema = (valid["close"] > valid["ema_50"]).sum()
        ratio = above_ema / len(valid)

        if self.explain:
            print(
                f"[MacroTrend] above_ema={above_ema}/{len(valid)} "
                f"({ratio:.0%})"
            )

        if ratio >= REQUIRED_RATIO:
            return MacroTrend.ALIVE
        else:
            return MacroTrend.DEAD


    def _classify_distribution_stage(self) -> DistributionStage:
        """
        是否進入派發結構（中週期）
        使用 1h RSI + ATR 變化
        """
        df = self.df_1h.dropna()

        if len(df) < 50:
            return DistributionStage.NONE

        rsi = df["rsi"].iloc[-1]
        atr_now = df["atr"].iloc[-1]
        atr_prev = df["atr"].iloc[-20]

        if rsi > 70 and atr_now > atr_prev:
            return DistributionStage.CONFIRMED

        if rsi > 60:
            return DistributionStage.EARLY

        return DistributionStage.NONE

    def _classify_capital_posture(
        self,
        macro_trend: MacroTrend,
        distribution: DistributionStage,
    ) -> CapitalPosture:
        """
        世界資金姿態（只決定能不能動）
        """
        if macro_trend == MacroTrend.DEAD:
            return CapitalPosture.CASH_BIASED

        if distribution == DistributionStage.CONFIRMED:
            return CapitalPosture.CASH_BIASED

        if distribution == DistributionStage.EARLY:
            return CapitalPosture.NEUTRAL

        return CapitalPosture.RISK_ON

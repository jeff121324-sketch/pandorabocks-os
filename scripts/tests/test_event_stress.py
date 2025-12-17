import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor

from pandora_core.pandora_runtime import PandoraRuntime
from trading_core.perception.market_adapter import MarketKlineAdapter


# ----------------------------------------
# ✔ Zero-PBEvent: Fastest structure (skips PBEvent construction)
# ----------------------------------------
class ZeroPBEvent:
    __slots__ = ("type", "payload", "ts")

    def __init__(self, type, payload, ts):
        self.type = type
        self.payload = payload
        self.ts = ts


# ----------------------------------------
# ✔ Normalize timestamp to float
# ----------------------------------------
def normalize_ts(raw_ts):
    if isinstance(raw_ts, float) or isinstance(raw_ts, int):
        return float(raw_ts)
    try:
        return float(pd.Timestamp(raw_ts).timestamp())
    except:
        return time.time()


# ----------------------------------------
# ✔ Emit (single record)
# ----------------------------------------
def emit_one(rt, adapter, row, symbol, interval, fast=False, zero_event=False, skip_validator=False):
    raw = row.to_dict()
    raw["symbol"] = symbol
    raw["interval"] = interval
    raw["ts"] = normalize_ts(raw.get("timestamp", raw.get("ts")))

    if zero_event:
        event = ZeroPBEvent("market.kline", raw, raw["ts"])
        rt.fast_bus.publish(event)
        return

    # Normal adapter → PBEvent
    if skip_validator:
        event = adapter.to_event_no_validate(raw)
    else:
        event = adapter.to_event(raw)

    if fast:
        rt.fast_bus.publish(event)
    else:
        rt.bus.publish(event)


# ----------------------------------------
# ✔ Batch Emit
# ----------------------------------------
def emit_batch(rt, df, symbol, interval, batch=50, **opts):
    adapter = rt.adapters["market"]
    rows = df.iterrows()
    buffer = []

    for _, row in rows:
        buffer.append(row)

        if len(buffer) >= batch:
            for r in buffer:
                emit_one(rt, adapter, r, symbol, interval, **opts)
            buffer.clear()

    # flush remainder
    for r in buffer:
        emit_one(rt, adapter, r, symbol, interval, **opts)


# ----------------------------------------
# ✔ Multi-thread Emit (3 sources)
# ----------------------------------------
def emit_parallel(rt, dfs, symbol, intervals, **opts):
    with ThreadPoolExecutor(max_workers=3) as pool:
        for df, itv in zip(dfs, intervals):
            pool.submit(emit_batch, rt, df, symbol, itv, **opts)


# ----------------------------------------
# ✔ Mode Runner (timer wrapper)
# ----------------------------------------
def run_mode(title, func):
    print(f"\n=== 🚀 {title} ===")
    t0 = time.time()
    total_events = func()
    dt = time.time() - t0
    rate = int(total_events / dt)

    print(f"Total Events: {total_events}")
    print(f"Time: {dt:.4f} sec")
    print(f"Throughput: {rate:,} events/sec")
    print("================================")
    return rate


# =======================================================
#                       MAIN
# =======================================================
def main():

    print("[Load] Loading test datasets...")
    df15 = pd.read_csv("test_data/BTC_USDT_15m.csv")
    df1h = pd.read_csv("test_data/BTC_USDT_1h.csv")
    df4h = pd.read_csv("test_data/BTC_USDT_4h.csv")

    # Initialize Pandora Runtime (Zero-Copy enabled)
    rt = PandoraRuntime(".")
    rt.register_adapter("market", MarketKlineAdapter())

    print("[Pandora] Runtime initialized.")

    total_15 = len(df15)
    total_parallel = len(df15) + len(df1h) + len(df4h)

    # ------------------- Mode A -------------------
    run_mode("Mode A: Batch x50 (Optimized)", lambda:
        (emit_batch(rt, df15, "BTC/USDT", "15m", batch=50), total_15)[1]
    )

    # ------------------- Mode B -------------------
    run_mode("Mode B: Multi-thread (3 Sources)", lambda:
        (emit_parallel(rt, [df15, df1h, df4h], "BTC/USDT", ["15m", "1h", "4h"]), total_parallel)[1]
    )

    # ------------------- Mode C -------------------
    adapter = rt.adapters["market"]
    adapter.to_event_no_validate = lambda raw: adapter.to_event(raw)  # temporary fast path

    run_mode("Mode C: Zero-Validator (Skip Validation)", lambda:
        (emit_batch(rt, df15, "BTC/USDT", "15m", batch=50, skip_validator=True), total_15)[1]
    )

    # ------------------- Mode D -------------------
    run_mode("Mode D: Zero-PBEvent (Fastest Possible)", lambda:
        (emit_batch(rt, df15, "BTC/USDT", "15m", batch=50, zero_event=True), total_15)[1]
    )


if __name__ == "__main__":
    main()




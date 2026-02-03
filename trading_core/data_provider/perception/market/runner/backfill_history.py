import time
from trading_core.data_provider.perception.market.binance.binance_fetcher import (
    BinanceRawFetcher
)
from trading_core.data_provider.perception.market.storage.csv_market_writer import (
    MarketCSVWriter
)
def detect_kline_gaps(records: list[dict], interval: str) -> list[tuple[int, int]]:
    """
    偵測缺失的 K 線時間區間
    回傳 [(from_ts, to_ts), ...]（秒）
    """
    if not records:
        return []

    interval_sec_map = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "4h": 14400,
        "1d": 86400,
    }

    if interval not in interval_sec_map:
        raise ValueError(f"Unsupported interval: {interval}")

    step = interval_sec_map[interval]

    records = sorted(records, key=lambda r: r["open_time"])

    gaps = []
    prev = None

    for r in records:
        if prev is not None:
            expected_open = prev["open_time"] + step
            if expected_open < r["open_time"]:
                gaps.append((expected_open, r["open_time"] - step))
        prev = r

    return gaps

def _normalize_record(r: dict) -> dict:
    """
    將 Binance 各種可能的 kline schema
    統一轉成 v1.7 標準 schema（秒）
    """

    # open / close time（秒）
    if "open_time" in r:
        open_ts = int(float(r["open_time"]))
    elif "kline_open_ts" in r:
        open_ts = int(float(r["kline_open_ts"]))
    elif "open_time_ms" in r:
        open_ts = int(float(r["open_time_ms"]) / 1000)
    else:
        raise KeyError("open_time")

    if "close_time" in r:
        close_ts = int(float(r["close_time"]))
    elif "kline_close_ts" in r:
        close_ts = int(float(r["kline_close_ts"]))
    elif "close_time_ms" in r:
        close_ts = int(float(r["close_time_ms"]) / 1000)
    else:
        raise KeyError("close_time")

    return {
        "open_time": open_ts,     # ⭐ 秒
        "close_time": close_ts,   # ⭐ 秒
        "open": float(r["open"]),
        "high": float(r["high"]),
        "low": float(r["low"]),
        "close": float(r["close"]),
        "volume": float(r["volume"]),
    }

def backfill(
    symbol: str,
    interval: str,
    from_ts: int,
    to_ts: int,
    csv_root: str,
    provider=None,
):
    print(f"🔄 Backfill {symbol} {interval} from {from_ts} → {to_ts}")

    fetcher = BinanceRawFetcher()
    writer = MarketCSVWriter(root=csv_root)

    # =====================================================
    # ✅ Step 0: 讀取既有 CSV（關鍵）
    # =====================================================
    existing_records = []
    try:
        existing_raw = writer.read(symbol=symbol, interval=interval)
        for r in existing_raw:
            try:
                existing_records.append(_normalize_record(r))
            except Exception:
                pass
    except Exception:
        pass  # CSV 不存在也沒關係

    # =====================================================
    # ✅ Step 1: 檢查 CSV 是否損壞
    # =====================================================
    bad_start, bad_end = detect_corrupted_ranges(existing_records)

    if bad_start is not None:
        print(f"🚨 Corrupted CSV detected: {bad_start} → {bad_end}")
        from_ts = bad_start  # ⬅️ 關鍵：整段重建

    # =====================================================
    # ✅ Step 2: 抓歷史資料（真實市場）
    # =====================================================
    raw_records = fetcher.fetch_history(
        symbol=symbol,
        interval=interval,
        since_ts=from_ts,
        until_ts=to_ts,
    )

    fetched_records = []
    for r in raw_records:
        try:
            fetched_records.append(_normalize_record(r))
        except Exception as e:
            print(f"[Backfill] ⚠ normalize skip: {e}")

    # =====================================================
    # ✅ Step 3: 合併 existing + fetched
    # =====================================================
    records = existing_records + fetched_records

    if not records:
        print("ℹ️ No valid records")
        return

    # =====================================================
    # ✅ Step 4: 偵測整體時間軸的 gap
    # =====================================================
    gaps = detect_kline_gaps(records, interval)

    # =====================================================
    # ✅ Step 5: 修復 gap（抓真實資料）
    # =====================================================
    for gap_from, gap_to in gaps:
        print(f"🧩 Repair gap {symbol} {interval}: {gap_from} → {gap_to}")

        missing_raw = fetcher.fetch_history(
            symbol=symbol,
            interval=interval,
            since_ts=gap_from,
            until_ts=gap_to,
        )

        for r in missing_raw:
            try:
                records.append(_normalize_record(r))
            except Exception:
                pass

    # =====================================================
    # ✅ Step 6: 排序 + 去重（時間軸唯一）
    # =====================================================
    dedup = {}
    for r in records:
        dedup[r["open_time"]] = r

    records = sorted(dedup.values(), key=lambda r: r["open_time"])

    # =====================================================
    # ✅ Step 7: 一次性寫 CSV
    # =====================================================
    writer.write(records, symbol=symbol, interval=interval)

    # =====================================================
    # ✅ Step 8:（可選）emit history
    # =====================================================
    if provider is not None:
        for r in records:
            try:
                provider.emit_kline(
                    symbol=symbol,
                    interval=interval,
                    open_time_ms=int(r["open_time"] * 1000),
                    close_time_ms=int(r["close_time"] * 1000),
                    open_price=r["open"],
                    high_price=r["high"],
                    low_price=r["low"],
                    close_price=r["close"],
                    volume=r["volume"],
                    source="history",
                )
            except Exception:
                pass

    print(f"✅ Backfill done: {len(records)} records")
    time.sleep(1)


def detect_corrupted_ranges(records: list[dict]) -> tuple[int | None, int | None]:
    """
    回傳 (bad_start_ts, bad_end_ts)
    """
    seen = {}
    bad_times = []

    for r in records:
        ot = r.get("open_time")

        # 欄位不完整
        if any(r.get(k) is None for k in ["open", "high", "low", "close", "volume"]):
            bad_times.append(ot)
            continue

        # 重複時間
        if ot in seen:
            bad_times.append(ot)
        else:
            seen[ot] = r

    if not bad_times:
        return None, None

    return min(bad_times), max(bad_times)

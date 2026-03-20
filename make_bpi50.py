#!/usr/bin/env python3
"""
BPI=50になるようにwrを探索するスクリプト

wr候補をT(ノーツx2)から1ずつ下げていき、
scoreから算出したBPIが50に最も近いwrを採用する（バイナリサーチ）。
"""

import csv
import json
import math

COL_TITLE = 1
COL_ANOTHER_SCORE = 27
COL_LEGG_SCORE = 34

DIFF_MAP = {
    "4": ("another", COL_ANOTHER_SCORE),
    "10": ("leggendaria", COL_LEGG_SCORE),
}

def load_scores(csv_path):
    scores = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 35:
                continue
            title = row[COL_TITLE]
            for _, (chart_type, col) in DIFF_MAP.items():
                try:
                    score = int(row[col])
                    if score > 0:
                        scores[(title, chart_type)] = score
                except (ValueError, IndexError):
                    pass
    return scores

def calc_bpi(score, avg, wr, notes, coef=1.5):
    """BPIを計算する"""
    T = notes * 2
    if T <= score or T <= avg or T <= wr:
        return None
    s_prime = (T - avg) / (T - score)
    z_prime = (T - avg) / (T - wr)
    if s_prime <= 0 or z_prime <= 0 or z_prime == 1:
        return None
    ratio = math.log(s_prime) / math.log(z_prime)
    sign = 1 if ratio >= 0 else -1
    return 100 * sign * abs(ratio) ** coef

def find_wr_for_bpi50(score, avg, notes, coef=1.5):
    """BPI=50に最も近いwrをバイナリサーチで探す"""
    T = notes * 2
    if score <= avg or score >= T or avg <= 0:
        return None

    lo, hi = score + 1, T

    bpi_lo = calc_bpi(score, avg, lo, notes, coef)
    bpi_hi = calc_bpi(score, avg, hi - 1, notes, coef)

    if bpi_lo is None or bpi_hi is None:
        return None
    if bpi_lo < 50:
        return None

    while lo < hi - 1:
        mid = (lo + hi) // 2
        b = calc_bpi(score, avg, mid, notes, coef)
        if b is None:
            break
        if b > 50:
            lo = mid
        else:
            hi = mid

    b_lo = calc_bpi(score, avg, lo, notes, coef) or float('inf')
    b_hi = calc_bpi(score, avg, hi, notes, coef) or float('inf')
    if abs(b_lo - 50) <= abs(b_hi - 50):
        return lo
    return hi

def main():
    scores = load_scores("score.csv")
    print(f"score.csvから {len(scores)} 件のスコアを読み込みました")

    with open("bpi_raw.json", encoding="utf-8") as f:
        bpi_data = json.load(f)
    songs = bpi_data.get("body", bpi_data) if isinstance(bpi_data, dict) else bpi_data

    result = []
    skipped_below_avg = 0
    skipped_no_score = 0
    skipped_other = 0

    for entry in songs:
        title = entry.get("title", "")
        diff = str(entry.get("difficulty", ""))

        if diff not in DIFF_MAP:
            skipped_other += 1
            continue

        chart_type, _ = DIFF_MAP[diff]
        key = (title, chart_type)

        if key not in scores:
            skipped_no_score += 1
            continue

        score = scores[key]
        avg = entry.get("avg", -1)
        notes = entry.get("notes", 0)
        coef_val = entry.get("coef", -1)
        coef = 1.5 if coef_val == -1 else float(coef_val)

        if avg <= 0:
            skipped_below_avg += 1
            continue

        wr = find_wr_for_bpi50(score, avg, notes, coef)
        if wr is None:
            skipped_below_avg += 1
            continue

        new_entry = dict(entry)
        new_entry["wr"] = wr
        result.append(new_entry)

    print(f"結果: {len(result)} 件")
    print(f"スキップ (avg以下): {skipped_below_avg} 件")
    print(f"スキップ (スコアなし): {skipped_no_score} 件")
    print(f"スキップ (DP等): {skipped_other} 件")

    output = {
        "version": bpi_data.get("version", "") if isinstance(bpi_data, dict) else "",
        "requireVersion": bpi_data.get("requireVersion", 0) if isinstance(bpi_data, dict) else 0,
        "body": result,
    }

    with open("bpi50.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("\n出力: bpi50.json")

if __name__ == "__main__":
    main()

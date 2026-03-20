#!/usr/bin/env python3
"""
BPI=50になるようにwrを逆算するスクリプト

公式: BPI = 100 * ln(S') / ln(Z')  where
  PGF(x) = 0.5 / (1 - x)
  S' = PGF(score/T) / PGF(avg/T) = (T - avg) / (T - score)
  Z' = PGF(wr/T) / PGF(avg/T)   = (T - avg) / (T - wr)
  T = notes * 2 (理論最大スコア)

BPI=50 → Z' = S'^2 → wr = T - (T - score)^2 / (T - avg)
"""

import csv
import json

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

def calc_wr_for_bpi50(score, avg, notes):
    """BPI=50になるwrを計算する"""
    T = notes * 2
    if score <= avg:
        return None  # BPI<=0になるので不可
    if T <= avg or T <= score:
        return None  # 異常値
    wr = T - (T - score) ** 2 / (T - avg)
    wr_int = round(wr)
    # バリデーション: avg < score < wr <= T
    if wr_int <= score or wr_int > T:
        return None
    return wr_int

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

        if avg <= 0:
            skipped_below_avg += 1
            continue

        wr = calc_wr_for_bpi50(score, avg, notes)
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

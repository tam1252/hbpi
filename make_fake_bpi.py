#!/usr/bin/env python3
"""
BPI定義の偽定義生成スクリプト
- score.csvのスコアでwrを置き換える
- score.csvにない曲は削除する
"""

import csv
import json

# score.csvのカラムインデックス
COL_TITLE = 1
COL_ANOTHER_SCORE = 27
COL_LEGG_SCORE = 34

# BPI difficulty -> (chart_type, score_column)
DIFF_MAP = {
    "4": ("another", COL_ANOTHER_SCORE),
    "10": ("leggendaria", COL_LEGG_SCORE),
}

def load_scores(csv_path):
    """score.csvからスコアを読み込む。key=(title, chart_type), value=score"""
    scores = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # header skip
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

def main():
    scores = load_scores("score.csv")
    print(f"score.csvから {len(scores)} 件のスコアを読み込みました")

    with open("bpi_raw.json", encoding="utf-8") as f:
        bpi_data = json.load(f)

    songs = bpi_data.get("body", bpi_data) if isinstance(bpi_data, dict) else bpi_data
    print(f"BPIデータ: {len(songs)} 件")

    result = []
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

        new_entry = dict(entry)
        new_entry["wr"] = scores[key]
        result.append(new_entry)

    print(f"結果: {len(result)} 件")
    print(f"スキップ (スコアなし): {skipped_no_score} 件")
    print(f"スキップ (DP等): {skipped_other} 件")

    output = {
        "version": bpi_data.get("version", "") if isinstance(bpi_data, dict) else "",
        "requireVersion": bpi_data.get("requireVersion", 0) if isinstance(bpi_data, dict) else 0,
        "body": result,
    }

    output_path = "hbpi.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n出力: {output_path}")

if __name__ == "__main__":
    main()

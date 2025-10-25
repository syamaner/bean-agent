#!/usr/bin/env python3
"""
Convert Label Studio JSON export to our annotation format.

Usage:
  python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/project-EXPORT.json \
    --output data/labels

Output: One JSON per audio file in the output directory.
"""
import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import librosa

OUR_SAMPLE_RATE = 44100


def strip_hash_prefix(filename: str) -> str:
    """Label Studio may prefix file uploads with a hash and a dash.
    Example: 0d93a737-roast-1.wav -> roast-1.wav
    """
    if "-" in filename:
        return filename.split("-", 1)[1]
    return filename


def convert_task(task: Dict[str, Any], data_root: Path) -> Dict[str, Any]:
    # Determine audio file name from task data
    # Prefer 'file_upload' if present; else parse from data.audio
    file_upload = task.get("file_upload")
    if file_upload:
        hashed_name = Path(file_upload).name
    else:
        audio_path = task.get("data", {}).get("audio", "")
        hashed_name = Path(audio_path).name

    original_name = strip_hash_prefix(hashed_name)
    local_audio_path = data_root / original_name

    # Compute duration (seconds)
    try:
        duration = librosa.get_duration(path=str(local_audio_path))
    except Exception:
        duration = None

    # Extract annotation results
    annotations: List[Dict[str, Any]] = []
    ann_list = task.get("annotations") or []
    for ann in ann_list:
        results = ann.get("result") or []
        for r in results:
            if r.get("type") == "labels" and "value" in r:
                val = r["value"]
                labels = val.get("labels") or []
                if not labels:
                    continue
                annotations.append({
                    "id": f"chunk_{len(annotations):03d}",
                    "start_time": float(val.get("start", 0.0)),
                    "end_time": float(val.get("end", 0.0)),
                    "label": str(labels[0]),
                    "confidence": "high",
                })

    return {
        "audio_file": original_name,
        "duration": duration if duration is not None else 0.0,
        "sample_rate": OUR_SAMPLE_RATE,
        "annotations": annotations,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to Label Studio JSON export")
    parser.add_argument("--output", required=True, help="Directory to write per-file annotations")
    parser.add_argument("--data-root", default="data/raw", help="Local directory where WAV files live")
    args = parser.parse_args()

    export_path = Path(args.input)
    out_dir = Path(args.output)
    data_root = Path(args.data_root)

    out_dir.mkdir(parents=True, exist_ok=True)

    with export_path.open("r") as f:
        exported = json.load(f)

    # exported is a list of tasks
    converted_count = 0
    for task in exported:
        converted = convert_task(task, data_root)
        stem = Path(converted["audio_file"]).stem
        out_path = out_dir / f"{stem}.json"
        with out_path.open("w") as f:
            json.dump(converted, f, indent=2)
        print(f"Wrote {out_path}")
        converted_count += 1

    print(f"Converted {converted_count} tasks -> {out_dir}")


if __name__ == "__main__":
    main()

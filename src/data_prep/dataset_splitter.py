#!/usr/bin/env python3
"""
Split audio chunks into train/validation/test sets with stratification.

Ensures balanced class distribution across all splits.

Usage:
  python src/data_prep/dataset_splitter.py \
    --input data/processed \
    --output data/splits \
    --train 0.7 --val 0.15 --test 0.15 \
    --seed 42
"""
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from sklearn.model_selection import train_test_split


def collect_files_by_label(input_dir: Path) -> Dict[str, List[Path]]:
    """Collect all audio files grouped by label."""
    files_by_label = {}
    
    for label_dir in input_dir.iterdir():
        if label_dir.is_dir() and not label_dir.name.startswith('.'):
            label = label_dir.name
            files = sorted(label_dir.glob('*.wav'))
            files_by_label[label] = files
            print(f"Found {len(files)} files for label: {label}")
    
    return files_by_label


def stratified_split(
    files_by_label: Dict[str, List[Path]],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    random_seed: int
) -> Tuple[Dict[str, List[Path]], Dict[str, List[Path]], Dict[str, List[Path]]]:
    """
    Split files into train/val/test with stratification.
    
    Returns:
        (train_files, val_files, test_files) each as dict[label] -> list[paths]
    """
    train_files = {}
    val_files = {}
    test_files = {}
    
    for label, files in files_by_label.items():
        # First split: separate out test set
        train_val, test = train_test_split(
            files,
            test_size=test_ratio,
            random_state=random_seed
        )
        
        # Second split: separate train and val from remaining
        # Adjust val ratio relative to train_val size
        val_ratio_adjusted = val_ratio / (train_ratio + val_ratio)
        train, val = train_test_split(
            train_val,
            test_size=val_ratio_adjusted,
            random_state=random_seed
        )
        
        train_files[label] = train
        val_files[label] = val
        test_files[label] = test
        
        print(f"\n{label}:")
        print(f"  Train: {len(train)} ({len(train)/len(files)*100:.1f}%)")
        print(f"  Val:   {len(val)} ({len(val)/len(files)*100:.1f}%)")
        print(f"  Test:  {len(test)} ({len(test)/len(files)*100:.1f}%)")
    
    return train_files, val_files, test_files


def copy_files_to_split(
    files_by_label: Dict[str, List[Path]],
    output_dir: Path,
    split_name: str
):
    """Copy files to their split directory."""
    split_dir = output_dir / split_name
    
    for label, files in files_by_label.items():
        label_dir = split_dir / label
        label_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            dest = label_dir / file_path.name
            shutil.copy2(file_path, dest)
    
    print(f"  ✅ Copied {sum(len(f) for f in files_by_label.values())} files to {split_dir}")


def generate_split_report(
    output_dir: Path,
    train_files: Dict[str, List[Path]],
    val_files: Dict[str, List[Path]],
    test_files: Dict[str, List[Path]]
):
    """Generate detailed split statistics report."""
    
    def count_by_label(files_dict):
        return {label: len(files) for label, files in files_dict.items()}
    
    train_counts = count_by_label(train_files)
    val_counts = count_by_label(val_files)
    test_counts = count_by_label(test_files)
    
    total_train = sum(train_counts.values())
    total_val = sum(val_counts.values())
    total_test = sum(test_counts.values())
    total_all = total_train + total_val + total_test
    
    report_lines = [
        "# Dataset Split Report",
        "",
        "## Split Configuration",
        "",
        f"- **Train**: {total_train} samples ({total_train/total_all*100:.1f}%)",
        f"- **Validation**: {total_val} samples ({total_val/total_all*100:.1f}%)",
        f"- **Test**: {total_test} samples ({total_test/total_all*100:.1f}%)",
        f"- **Total**: {total_all} samples",
        "",
        "## Class Distribution",
        "",
        "### Train Set",
        "",
    ]
    
    for label in train_counts.keys():
        count = train_counts[label]
        pct = (count / total_train * 100) if total_train > 0 else 0
        report_lines.append(f"- **{label}**: {count} samples ({pct:.1f}%)")
    
    report_lines.extend([
        "",
        "### Validation Set",
        "",
    ])
    
    for label in val_counts.keys():
        count = val_counts[label]
        pct = (count / total_val * 100) if total_val > 0 else 0
        report_lines.append(f"- **{label}**: {count} samples ({pct:.1f}%)")
    
    report_lines.extend([
        "",
        "### Test Set",
        "",
    ])
    
    for label in test_counts.keys():
        count = test_counts[label]
        pct = (count / total_test * 100) if total_test > 0 else 0
        report_lines.append(f"- **{label}**: {count} samples ({pct:.1f}%)")
    
    # Comparison table
    report_lines.extend([
        "",
        "## Split Comparison",
        "",
        "| Label | Train | Val | Test | Total |",
        "|-------|-------|-----|------|-------|",
    ])
    
    for label in train_counts.keys():
        t = train_counts[label]
        v = val_counts[label]
        te = test_counts[label]
        total = t + v + te
        report_lines.append(f"| {label} | {t} | {v} | {te} | {total} |")
    
    # Ratios
    report_lines.extend([
        "",
        "## Class Balance (within each split)",
        "",
    ])
    
    for split_name, counts, total in [
        ("Train", train_counts, total_train),
        ("Validation", val_counts, total_val),
        ("Test", test_counts, total_test)
    ]:
        report_lines.append(f"### {split_name}")
        report_lines.append("")
        for label, count in counts.items():
            pct = (count / total * 100) if total > 0 else 0
            report_lines.append(f"- {label}: {pct:.1f}%")
        report_lines.append("")
    
    # Save report
    report_path = output_dir / 'split_report.md'
    report_path.write_text('\n'.join(report_lines))
    print(f"\n📊 Split report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Split dataset into train/val/test with stratification'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/processed'),
        help='Input directory with labeled audio chunks'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/splits'),
        help='Output directory for splits'
    )
    parser.add_argument(
        '--train',
        type=float,
        default=0.7,
        help='Train split ratio (default: 0.7)'
    )
    parser.add_argument(
        '--val',
        type=float,
        default=0.15,
        help='Validation split ratio (default: 0.15)'
    )
    parser.add_argument(
        '--test',
        type=float,
        default=0.15,
        help='Test split ratio (default: 0.15)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    args = parser.parse_args()
    
    # Validate ratios
    total_ratio = args.train + args.val + args.test
    if not (0.99 <= total_ratio <= 1.01):  # Allow small floating point error
        print(f"❌ Error: Split ratios must sum to 1.0 (got {total_ratio})")
        return
    
    print("📊 Dataset Splitter")
    print("=" * 50)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Ratios: Train={args.train}, Val={args.val}, Test={args.test}")
    print(f"Random seed: {args.seed}")
    print()
    
    # Collect files
    files_by_label = collect_files_by_label(args.input)
    
    if not files_by_label:
        print("❌ No labeled directories found in input directory")
        return
    
    total_files = sum(len(files) for files in files_by_label.values())
    print(f"\nTotal files: {total_files}")
    
    # Perform stratified split
    print("\n🔀 Performing stratified split...")
    train_files, val_files, test_files = stratified_split(
        files_by_label,
        args.train,
        args.val,
        args.test,
        args.seed
    )
    
    # Copy files to split directories
    print("\n📁 Copying files to split directories...")
    copy_files_to_split(train_files, args.output, 'train')
    copy_files_to_split(val_files, args.output, 'val')
    copy_files_to_split(test_files, args.output, 'test')
    
    # Generate report
    generate_split_report(args.output, train_files, val_files, test_files)
    
    print("\n✅ Dataset split complete!")
    print(f"   Train: {args.output}/train/")
    print(f"   Val:   {args.output}/val/")
    print(f"   Test:  {args.output}/test/")


if __name__ == '__main__':
    main()

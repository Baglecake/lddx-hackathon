"""
Evaluator wrapper for Gemma 4 pipeline output.

Converts the Gemma/hackathon export format to the format expected by
ddx_evaluator.py, then runs the same deterministic evaluation.

The Gemma format uses top-level keys (pipeline_diagnoses, voting_result,
rounds, etc.) while the evaluator expects them nested under 'results'.

Usage:
    python benchmark/evaluate_gemma.py --results-dir /path/to/gemma/exports --dataset pipeline/data/Open-XDDx.xlsx
    python benchmark/evaluate_gemma.py --results-dir /path/to/gemma/exports --dataset pipeline/data/Open-XDDx.xlsx --output results/gemma4_eval.json
"""

import os
import sys
import json
import shutil
import tempfile
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


def convert_gemma_to_qwen(gemma_path: str) -> dict:
    """Convert a Gemma export JSON to the format ddx_evaluator expects."""
    with open(gemma_path) as f:
        g = json.load(f)

    # The evaluator expects:
    #   case_index, case (dict with name/specialty), ground_truth (dict),
    #   results (dict with final_diagnoses, voting_result, rounds, etc.),
    #   specialists, duration_seconds

    # Build the 'results' dict from either full_results or top-level keys
    full_results = g.get('full_results', {})

    results = {
        'rounds': full_results.get('rounds', g.get('rounds', {})),
        'final_diagnoses': full_results.get('final_diagnoses', g.get('pipeline_diagnoses', [])),
        'voting_result': full_results.get('voting_result', g.get('voting_result', {})),
        'credibility_scores': full_results.get('credibility_scores', g.get('credibility_scores', {})),
        'total_duration': full_results.get('total_duration', g.get('total_duration', 0)),
        'case': full_results.get('case', {}),
    }

    # Build the case dict
    case_index = g.get('case_index', 0)
    case = {
        'name': f"case_{case_index:03d}",
        'description': g.get('patient_info', '')[:500],
        'specialty': g.get('specialty', 'Unknown'),
    }

    # Ground truth — could be dict or list
    ground_truth = g.get('ground_truth', {})
    if isinstance(ground_truth, list):
        ground_truth = {dx: [] for dx in ground_truth}

    converted = {
        'case_index': case_index,
        'case': case,
        'ground_truth': ground_truth,
        'results': results,
        'specialists': g.get('specialists', []),
        'duration_seconds': g.get('total_duration', 0),
        'timestamp': g.get('run_metadata', {}).get('timestamp', ''),
        'config': {
            'model': g.get('run_metadata', {}).get('model', 'unknown'),
            'pipeline_mode': g.get('run_metadata', {}).get('mode', 'full'),
        },
    }

    return converted


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Gemma 4 pipeline results using the standard ddx_evaluator"
    )
    parser.add_argument('--results-dir', required=True,
                        help='Directory with Gemma export case_*.json files')
    parser.add_argument('--dataset', default='data/Open-XDDx.xlsx',
                        help='Path to Open-XDDx dataset')
    parser.add_argument('--output', default=None,
                        help='Output path for evaluation report')
    args = parser.parse_args()

    results_dir = args.results_dir
    if not os.path.isabs(results_dir):
        results_dir = os.path.join(PROJECT_ROOT, results_dir)

    # Find all case files
    case_files = sorted(
        f for f in os.listdir(results_dir)
        if f.startswith('case_') and f.endswith('.json')
    )

    if not case_files:
        print(f"No case files found in {results_dir}")
        return

    print(f"Found {len(case_files)} Gemma case files")
    print(f"Converting to evaluator format...")

    # Create temp directory with converted files
    with tempfile.TemporaryDirectory() as tmp_dir:
        converted = 0
        for fname in case_files:
            src = os.path.join(results_dir, fname)
            try:
                qwen_format = convert_gemma_to_qwen(src)
                dst = os.path.join(tmp_dir, fname)
                with open(dst, 'w') as f:
                    json.dump(qwen_format, f, indent=2, default=str)
                converted += 1
            except Exception as e:
                print(f"  Warning: failed to convert {fname}: {e}")

        print(f"Converted {converted}/{len(case_files)} files")
        print(f"Running evaluator...\n")

        # Build evaluator command
        dataset_path = args.dataset
        if not os.path.isabs(dataset_path):
            dataset_path = os.path.join(PROJECT_ROOT, dataset_path)

        output_flag = ""
        if args.output:
            output_path = args.output
            if not os.path.isabs(output_path):
                output_path = os.path.join(PROJECT_ROOT, output_path)
            output_flag = f"--output {output_path}"

        evaluator = os.path.join(SCRIPT_DIR, 'ddx_evaluator.py')
        cmd = f"python {evaluator} --results-dir {tmp_dir} --dataset {dataset_path} {output_flag}"
        os.system(cmd)


if __name__ == '__main__':
    main()

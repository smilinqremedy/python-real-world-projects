"""
Command-Line Interface for AI News Article Summarization System.
"""
import argparse
import sys
import os
import json

from summarizer import ArticleSummarizer
from metrics import compute_rouge


def main():
    parser = argparse.ArgumentParser(description="AI News Article Summarization System")
    parser.add_argument("--input", type=str, help="Path to input text file")
    parser.add_argument("--text", type=str, help="Raw article text string")
    parser.add_argument("--mode", choices=["short", "detailed"], default="short", help="Summary length mode")
    parser.add_argument("--method", choices=["extractive", "abstractive"], default="extractive", help="Summarization technique")
    parser.add_argument("--output", type=str, default=None, help="Output path for summary")
    parser.add_argument("--format", choices=["txt", "json"], default="txt", help="Output format")
    parser.add_argument("--eval-ref", type=str, help="Reference gold summary to compute ROUGE scores against")

    args = parser.parse_args()
    summarizer = ArticleSummarizer()

    content = ""
    if args.input:
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    elif args.text:
        content = args.text

    if not content.strip():
        parser.print_help()
        return

    res = summarizer.summarize_article(content, mode=args.mode, method=args.method)
    if not res["success"]:
        print(f"Error: {res['error']}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"GENERATED SUMMARY ({args.mode.upper()} - {args.method.upper()}):")
    print("=" * 60)
    print(res["summary"])
    print(f"\nStats: {res['summary_word_count']} words (Compressed from {res['original_word_count']} words, {res['compression_ratio_pct']}%)")

    print("\nProminent Keywords:")
    for k in res["keywords"]:
        print(f"  - {k['keyword']} ({k['frequency']})")

    print("\nNamed Entities Recognized:")
    for cat, items in res["named_entities"].items():
        if items:
            print(f"  - {cat.capitalize()}: {', '.join(items)}")

    if args.eval_ref:
        rouge = compute_rouge(args.eval_ref, res["summary"])
        print("\nROUGE Evaluation Metrics:")
        print(f"  ROUGE-1 F1: {rouge['rouge_1']['f1'] * 100:.2f}%")
        print(f"  ROUGE-2 F1: {rouge['rouge_2']['f1'] * 100:.2f}%")
        print(f"  ROUGE-L F1: {rouge['rouge_l']['f1'] * 100:.2f}%")

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as out_f:
            if args.format == "json":
                json.dump(res, out_f, indent=2)
            else:
                out_f.write(res["summary"])
        print(f"\nSaved output to: {args.output}")


if __name__ == "__main__":
    main()

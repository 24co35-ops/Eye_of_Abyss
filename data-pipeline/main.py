"""Eye of Abyss — Synthetic training data generator CLI."""

import argparse
import sys


def cmd_generate(args):
    """Generate synthetic criminal actor profiles and export training data."""
    # ponytail: stub -- wire core/ generators and exporters/ when ready
    print(f"[generate] count={args.count} archetypes={args.archetypes} output={args.output_dir}")
    print("Not yet implemented. See data-pipeline/core/ for generators.")


def main():
    parser = argparse.ArgumentParser(description="Eye of Abyss data pipeline")
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate", help="Generate synthetic actor profiles")
    gen.add_argument("--count", type=int, default=100)
    gen.add_argument("--archetypes", nargs="+", default=["investment_fraudster"])
    gen.add_argument("--output-dir", default="./output")

    args = parser.parse_args()
    if args.command == "generate":
        cmd_generate(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

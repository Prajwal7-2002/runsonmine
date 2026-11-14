"""Generate empirical consumer silicon serving benchmarks and concurrency scaling curves."""

from pathlib import Path
from runsonmine.dataset import build_dataset


def main():
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "data" / "results"
    out_dir = root / "hf_dataset"
    servebench_file = root.parent / "servebench" / "results" / "quick-ollama-np4.json"

    print("Extracting empirical silicon benchmark runs...")
    n_master, n_scaling = build_dataset(results_dir, out_dir, servebench_file)
    print(f"✓ Generated {n_master} master benchmark points and {n_scaling} scaling curve points.")
    print(f"✓ Wrote Dataset Card: {out_dir / 'README.md'}")
    print("\n🎉 Consumer silicon benchmarks dataset successfully generated!")


if __name__ == "__main__":
    main()

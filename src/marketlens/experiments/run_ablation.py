"""CLI and standalone entry point for running the Phase 5 feature ablation study."""

import argparse
import sys
from marketlens.config import load_yaml_config
from marketlens.experiments.ablation import FeatureAblationRunner
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.experiments.run_ablation")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MarketLens AI Phase 5 Feature Ablation Study")
    parser.add_argument(
        "--config",
        type=str,
        default="phase5_experiments.yaml",
        help="Path to Phase 5 experiment YAML config.",
    )
    parser.add_argument(
        "--simulate-synthetic",
        action="store_true",
        help="Run simulation over synthetic test fixtures to verify E1-E3 pipeline mechanics.",
    )

    args = parser.parse_args()

    try:
        cfg = load_yaml_config(args.config)
        runner = FeatureAblationRunner(config=cfg)
        manifest, comparison_df = runner.run_ablation(
            allow_synthetic_simulation=args.simulate_synthetic,
        )

        print("\n================================================================================")
        print("                 PHASE 5 FEATURE ABLATION STUDY RESULTS                         ")
        print("================================================================================")
        print(comparison_df.to_string(index=False))
        print("================================================================================\n")
        print(f"Artifacts and run manifest saved to: {runner.tracking_dir}")
        return 0
    except Exception as e:
        logger.error(f"Feature ablation study failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

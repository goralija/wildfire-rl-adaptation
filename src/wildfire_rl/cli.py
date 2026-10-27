import argparse
import json
from pathlib import Path

from .evaluation import write_run


def main():
    parser = argparse.ArgumentParser(description='Run synthetic wildfire pilot baselines')
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='new output directory')
    args = parser.parse_args()
    try:
        manifest = write_run(json.loads(args.config.read_text()), args.out)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f'Wrote synthetic pilot to {args.out}; config {manifest["config_sha256"][:12]}')


if __name__ == '__main__':
    main()

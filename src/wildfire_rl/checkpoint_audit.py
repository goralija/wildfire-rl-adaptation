"""Read SB3 ZIP metadata without executing cloudpickle or torch serialization."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import zipfile


def audit_checkpoint(path):
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        if archive.getinfo('data').file_size > 4_000_000:
            raise ValueError('checkpoint metadata exceeds audit limit')
        data = json.loads(archive.read('data'))
        version = archive.read('_stable_baselines3_version').decode().strip()
        kwargs = data.get('policy_kwargs', {})
        if not isinstance(kwargs, dict):
            kwargs = {}
        return dict(file=path.name, size_bytes=path.stat().st_size,
                    sha256=sha256(path.read_bytes()).hexdigest(), sb3_version=version,
                    num_timesteps=data.get('num_timesteps'), n_steps=data.get('n_steps'),
                    features_extractor_class=kwargs.get('features_extractor_class'),
                    deserialized=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkpoint', type=Path, nargs='+')
    args = parser.parse_args()
    print(json.dumps([audit_checkpoint(path) for path in args.checkpoint], indent=2))


if __name__ == '__main__':
    main()

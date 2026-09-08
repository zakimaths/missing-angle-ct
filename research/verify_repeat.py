"""Compare saved probe arrays exactly, ignoring machine-dependent timings."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def verify(first, second):
    reports = [json.loads((p / 'results.json').read_text()) for p in (first, second)]
    with np.load(first / 'arrays.npz', allow_pickle=False) as a, np.load(second / 'arrays.npz', allow_pickle=False) as b:
        assert set(a.files) == set(b.files), 'Saved arrays differ'
        for name in a.files:
            x, y = a[name], b[name]
            assert x.shape == y.shape and x.dtype == y.dtype, name
            assert np.array_equal(x, y), f'{name}: values differ; exact repeatability not established'
            for val, report in zip((x, y), reports):
                actual = hashlib.sha256(np.ascontiguousarray(val).tobytes()).hexdigest()
                assert report['raw_array_sha256'][name] == actual, f'{name}: hash mismatch'
        print(f'PASS: all {len(a.files)} arrays match in shape, dtype, values and reported SHA-256.')
    print('This verifies these two runs only; it is not a cross-platform guarantee.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('first', type=Path)
    p.add_argument('second', type=Path)
    args = p.parse_args()
    verify(args.first, args.second)

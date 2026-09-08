"""Rebuild the bundled slice subset from a checksum-pinned public Slicer volume."""
from hashlib import sha256
import gzip
import json
from pathlib import Path
import sys

import numpy as np

EXPECTED = "4507b664690840abb6cb9af2d919377ffc4ef75b167cb6fd0f747befdb12e38e"
ROOT = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data-cache/CT-chest.nrrd"
raw = source.read_bytes()
if sha256(raw).hexdigest() != EXPECTED:
    raise ValueError("Source checksum mismatch; do not prepare unverified data")
header, compressed = raw.split(b"\n\n", 1)
fields = dict(line.split(": ", 1) for line in header.decode().splitlines()
              if ": " in line and not line.startswith("#"))
assert fields["type"] == "int" and fields["sizes"] == "512 512 139"
assert fields["endian"] == "little" and fields["encoding"] == "gzip"
decoded = gzip.decompress(compressed)
assert len(decoded) == 512*512*139*4
volume = np.frombuffer(decoded, dtype="<i4").reshape(139, 512, 512)
destination = ROOT / "src/missing_angle/data"
destination.mkdir(parents=True, exist_ok=True)
manifest = {
    "id": "slicer-ct-chest-v1", "title": "3D Slicer · CT Chest",
    "source_url": f"https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/{EXPECTED}",
    "source_sha256": EXPECTED, "original_shape_zyx": [139, 512, 512],
    "pixel_spacing_yx_mm": [0.76171898841857932, 0.76171898841857932],
    "slice_spacing_mm": 2.5, "space": fields["space"],
    "orientation": "Columns increase toward patient left; rows toward posterior; source array orientation retained.",
    "units": "HU", "licence": "3D Slicer licence, Part B; see SLICER-LICENSE.txt",
    "origin_note": "Public anonymised legacy sample. Acquiring hospital, patient demographics and diagnosis are not documented; no hospital affiliation or endorsement is asserted.",
    "modification": "Subset of eight axial slices; lossless int32-to-int16 conversion. Other volume metadata omitted. Reconstructions and normalised working images are derived products.",
    "slices": [],
}
for index in (16, 32, 48, 64, 80, 96, 112, 128):
    image = volume[index]
    assert image.min() >= -32768 and image.max() <= 32767
    filename = f"ct-chest-{index:03}.npy"
    np.save(destination / filename, image.astype("<i2"), allow_pickle=False)
    manifest["slices"].append({"index": index, "file": filename,
        "sha256": sha256((destination / filename).read_bytes()).hexdigest(),
        "pixel_sha256": sha256(image.astype("<i2").tobytes()).hexdigest(),
        "min_hu": int(image.min()), "max_hu": int(image.max())})
(destination / "ct-chest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
print(f"Prepared {len(manifest['slices'])} verified CT slices")

"""Local embedding and bounded import of acquired projection data."""
from io import BytesIO
import json
from pathlib import Path
import struct
import zlib

import numpy as np
from scipy.io import loadmat

WEB = Path(__file__).parent / 'web'
MAX_INPUT = 16 * 1024 * 1024
MAX_EXPANDED = 32 * 1024 * 1024


def _bounded_mat(raw):
    """Validate v5 element sizes and shapes before handing arrays to SciPy.

    A small compressed file can otherwise expand without a bound. Dimension
    checks also reject large declared arrays with an artificially short payload.
    No archive members are extracted and no MATLAB objects are instantiated.
    """
    if len(raw) < 128 or raw[126:128] not in (b'IM', b'MI'):
        raise ValueError('Choose an original HTC MATLAB v5 file.')
    endian = '<' if raw[126:128] == b'IM' else '>'
    expanded = 0
    count = 0

    def elements(data):
        offset = 0
        while offset < len(data):
            if len(data) - offset < 8:
                raise ValueError('Truncated MATLAB data element.')
            tag, length = struct.unpack_from(endian + 'II', data, offset)
            small = tag >> 16
            if small:
                short_type, small = struct.unpack_from(endian + 'HH', data, offset)
                if not 1 <= small <= 4:
                    raise ValueError('Invalid MATLAB data element.')
                yield short_type, data[offset + 4:offset + 4 + small]
                offset += 8
            else:
                end = offset + 8 + length
                if end > len(data):
                    raise ValueError('Truncated MATLAB data element.')
                yield tag, data[offset + 8:end]
                offset = end if tag == 15 else offset + 8 + ((length + 7) // 8) * 8

    def matrix(payload, depth=0):
        nonlocal count
        count += 1
        if depth > 12 or count > 10000:
            raise ValueError('MATLAB structure nesting exceeds the import limit.')
        fields = iter(elements(payload))
        try:
            ft, flags = next(fields)
            dt, dims = next(fields)
            nt, name = next(fields)
        except StopIteration as error:
            raise ValueError('Incomplete MATLAB array metadata.') from error
        if ft != 6 or len(flags) != 8 or dt != 5 or not 8 <= len(dims) <= 32 or len(dims) % 4 or nt != 1:
            raise ValueError('Invalid MATLAB array metadata.')
        flag_value = struct.unpack_from(endian + 'I', flags)[0]
        kind = flag_value & 0xff
        if kind not in (1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15):
            raise ValueError('MATLAB objects, functions and sparse arrays are not supported.')
        size = 1
        for dim in struct.unpack(endian + 'i' * (len(dims) // 4), dims):
            if dim < 0 or dim > 4_000_000:
                raise ValueError('MATLAB array dimensions exceed the import limit.')
            size *= dim
            if size > 4_000_000:
                raise ValueError('MATLAB array dimensions exceed the import limit.')
        rest = []
        for field in fields:
            if len(rest) >= 10000:
                raise ValueError('MATLAB field count exceeds the import limit.')
            rest.append(field)
        if kind in (6, 7, 8, 9, 10, 11, 12, 13, 14, 15):
            # MATLAB may store a declared double array using compact integer elements.
            widths = {1: 1, 2: 1, 3: 2, 4: 2, 5: 4, 6: 4, 7: 4, 9: 8, 12: 8, 13: 8}
            width = widths.get(rest[0][0]) if len(rest) == 1 else None
            if flag_value & 0x800 or width is None or len(rest[0][1]) != size * width:
                raise ValueError('MATLAB numeric payload does not match its declared dimensions.')
        if kind == 2:
            if len(rest) < 2 or rest[0][0] != 5 or len(rest[0][1]) != 4:
                raise ValueError('Invalid MATLAB structure field metadata.')
            field_width = struct.unpack_from(endian + 'i', rest[0][1])[0]
            if not 1 <= field_width <= 128 or rest[1][0] != 1 or len(rest[1][1]) > 16384 or len(rest[1][1]) % field_width:
                raise ValueError('MATLAB structure fields exceed the import limit.')
            expected_fields = size * (len(rest[1][1]) // field_width)
            if len(rest) - 2 != expected_fields or any(t != 14 for t, _ in rest[2:]):
                raise ValueError('MATLAB structure values do not match its declared fields.')
        if kind == 1 and (len(rest) != size or any(t != 14 for t, _ in rest)):
            raise ValueError('MATLAB cells do not match their declared dimensions.')
        for tag, content in rest:
            if tag == 14:
                matrix(content, depth + 1)
            elif tag == 15:
                raise ValueError('Nested compressed MATLAB elements are not supported.')

    output = bytearray(raw[:128])
    for tag, payload in elements(memoryview(raw)[128:]):
        if tag == 15:
            try:
                decoder = zlib.decompressobj()
                block = decoder.decompress(payload, MAX_EXPANDED - expanded + 1)
            except zlib.error as error:
                raise ValueError('Invalid compressed MATLAB data.') from error
            if len(block) + expanded > MAX_EXPANDED or decoder.unconsumed_tail:
                raise ValueError('Expanded MATLAB data exceeds the 32 MB limit.')
            if not decoder.eof or decoder.unused_data:
                raise ValueError('Incomplete or trailing compressed MATLAB data.')
        elif tag == 14:
            block = struct.pack(endian + 'II', tag, len(payload)) + payload.tobytes()
            block += b'\0' * (-len(block) % 8)
        else:
            raise ValueError('Unsupported MATLAB top-level element.')
        expanded += len(block)
        if expanded > MAX_EXPANDED:
            raise ValueError('Expanded MATLAB data exceeds the 32 MB limit.')
        for inner_tag, content in elements(memoryview(block)):
            if inner_tag != 14:
                raise ValueError('Expected a MATLAB array.')
            matrix(content)
        output.extend(block)
    return bytes(output)


def import_htc_mat(raw):
    """Read the documented HTC structure, not arbitrary scanner/raw-image formats."""
    if len(raw) > MAX_INPUT:
        raise ValueError('The MATLAB file exceeds the 16 MB input limit.')
    bounded = _bounded_mat(raw)
    data = loadmat(BytesIO(bounded), simplify_cells=True,
                   variable_names=['CtDataFull', 'CtDataLimited'])
    scan = data.get('CtDataFull', data.get('CtDataLimited'))
    if not isinstance(scan, dict) or 'parameters' not in scan:
        raise ValueError('Expected HTC2022 CtDataFull or CtDataLimited with scanner parameters.')
    p = scan['parameters']
    measured = np.asarray(scan['sinogram'], dtype=float)
    angles = np.asarray(p['angles'], dtype=float).reshape(-1)
    if measured.ndim != 2 or measured.shape[0] != len(angles) or not 4 <= len(angles) <= 1440:
        raise ValueError('Expected 4–1440 views, one sinogram row per angle.')
    if measured.shape[1] != int(p['numDetectorsPost']):
        raise ValueError('Detector count does not match the scanner metadata.')
    if not np.isfinite(measured).all() or not np.isfinite(angles).all():
        raise ValueError('Projection data contains non-finite values.')
    factor = 4 if measured.shape[1] == 560 else 1
    measured = measured.reshape(len(angles), -1, factor).mean(axis=2)
    if not 16 <= measured.shape[1] <= 512 or np.max(np.abs(measured)) > 100:
        raise ValueError('Unsupported detector count or line-integral range.')
    return {'schema': 'ct-projections/1', 'name': 'Imported HTC measurements', 'kind': 'measured',
            'angles_deg': angles.tolist(), 'sinogram': measured.tolist(),
            'geometry': {'type': 'fan', 'source_distance_mm': float(p['distanceSourceOrigin']),
                         'detector_distance_mm': float(p['distanceSourceDetector'] - p['distanceSourceOrigin']),
                         'detector_spacing_mm': float(p['pixelSizePost']) * factor,
                         'fov_mm': float(p['effectivePixelSizePost']) * 512},
            'source': {'preparation': f'HTC central-plane measurements; mean of {factor} adjacent log-transformed detector bins. All supplied angles preserved.'}}


def live_html(custom=None):
    inputs = {key: json.loads((WEB / 'projection-data' / f'{key}.json').read_text())
              for key in ('ta', 'tb', 'tc', 'chest-64', 'chest-96', 'abdomen-400', 'abdomen-480')}
    references = {key: json.loads((WEB / 'reference-data' / f'{key}.json').read_text())
                  for key in ('ta', 'tb', 'tc', 'chest-64', 'chest-96', 'abdomen-400', 'abdomen-480')}
    panel = (WEB / 'live-panel.html').read_text()
    if custom is not None:
        inputs['custom'] = custom
        panel = panel.replace('<option value="ta">', '<option value="custom">Imported HTC measurements</option><option value="ta">', 1)
    worker = (WEB / 'projection-core.js').read_text() + '\n' + (WEB / 'projection-worker.js').read_text()
    # Escape HTML-significant characters in data and code embedded in script strings.
    def script_json(value):
        return json.dumps(value, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>CT reconstruction lab</title>'
            '<style>body{margin:0;background:white}'+(WEB/'live.css').read_text()+'</style></head><body>'
            + '<main aria-label="CT reconstruction workspace">' + panel + '</main><script>window.CT_EMBEDDED_DATA='+script_json(inputs)+';window.CT_WORKER_CODE='
            + script_json(worker) + ';window.CT_EMBEDDED_REFERENCES=' + script_json(references) + ';</script><script>'+(WEB/'projection-core.js').read_text()
            + '</script><script>'+(WEB/'study.js').read_text()
            + '</script><script>'+(WEB/'live.js').read_text().replace("load('ta');", "load('custom');" if custom is not None else "load('ta');")+'</script></body></html>')

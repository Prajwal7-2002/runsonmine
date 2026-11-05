"""Peak memory bandwidth per GPU, used for the physical ceiling check.

Decode speed for one user cannot exceed (memory bandwidth / bytes of weights read per token).
The table holds vendor *peak* figures; where a product ships in several memory configurations,
the highest is used so that the ceiling stays an upper bound. Matching picks the longest key
found in the reported device name (lower-cased).
"""

from __future__ import annotations

# key (lower-case substring of the device name) -> peak memory bandwidth in GB/s
BANDWIDTH_GB_S: dict[str, float] = {
    # NVIDIA laptop and desktop (GeForce)
    "rtx 3050 6gb laptop": 168.0,
    "rtx 3050 laptop": 192.0,
    "rtx 3050": 224.0,
    "rtx 3060 laptop": 336.0,
    "rtx 3060": 360.0,
    "rtx 3070 laptop": 448.0,
    "rtx 3070": 448.0,
    "rtx 3080 laptop": 448.0,
    "rtx 3080": 760.0,
    "rtx 3090": 936.0,
    "rtx 4050 laptop": 192.0,
    "rtx 4060 laptop": 256.0,
    "rtx 4060 ti": 288.0,
    "rtx 4060": 272.0,
    "rtx 4070 laptop": 256.0,
    "rtx 4070 ti": 504.0,
    "rtx 4070": 504.0,
    "rtx 4080 laptop": 432.0,
    "rtx 4080 super": 736.0,
    "rtx 4080": 717.0,
    "rtx 4090 laptop": 576.0,
    "rtx 4090": 1008.0,
    "rtx 5090": 1792.0,
    # NVIDIA data centre / cloud
    "tesla t4": 320.0,
    "t4": 320.0,
    "p100": 732.0,
    "l40s": 864.0,
    "l40": 864.0,
    "l4": 300.0,
    "a10g": 600.0,
    "a10": 600.0,
    "a100": 2039.0,
    "h100": 3350.0,
    "h200": 4800.0,
    # Apple Silicon (unified memory; highest configuration of each chip)
    "apple m1 max": 400.0,
    "apple m1 pro": 200.0,
    "apple m1 ultra": 800.0,
    "apple m1": 68.0,
    "apple m2 max": 400.0,
    "apple m2 pro": 200.0,
    "apple m2 ultra": 800.0,
    "apple m2": 100.0,
    "apple m3 max": 400.0,
    "apple m3 pro": 150.0,
    "apple m3": 100.0,
    "apple m4 max": 546.0,
    "apple m4 pro": 273.0,
    "apple m4": 120.0,
}


def peak_bandwidth(device_name: str | None) -> float | None:
    """Peak memory bandwidth (GB/s) for a reported device name, or None if unknown."""
    if not device_name:
        return None
    name = device_name.lower()
    for key in sorted(BANDWIDTH_GB_S, key=len, reverse=True):
        if key in name:
            return BANDWIDTH_GB_S[key]
    return None

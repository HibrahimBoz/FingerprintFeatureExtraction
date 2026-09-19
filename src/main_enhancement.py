# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 11:42:58 2016

@author: utkarsh
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
import skimage.draw
import skimage.measure
import skimage.morphology

from getTerminationBifurcation import getTerminationBifurcation
from image_enhance import image_enhance
from removeSpuriousMinutiae import removeSpuriousMinutiae

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IMAGE = PROJECT_ROOT / "images" / "parmak izi 1.bmp"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "enhanced"


def _load_and_resize(image_path, target_rows=540):
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    rows, cols = img.shape
    aspect_ratio = rows / cols
    new_rows = target_rows
    new_cols = int(round(new_rows / aspect_ratio))
    return cv2.resize(img, (new_cols, new_rows), interpolation=cv2.INTER_LINEAR)


def _normalize_to_uint8(array):
    array = np.asarray(array, dtype=np.float64)
    lo, hi = array.min(), array.max()
    if hi - lo < 1e-9:
        return np.zeros_like(array, dtype=np.uint8)
    return ((array - lo) / (hi - lo) * 255).astype(np.uint8)


def _minutiae_angle_degrees(orientation_image, row, col):
    # Ridge orientation is only defined modulo pi, so the angle is reported
    # in the 0-180 range rather than a full 0-360 direction.
    return float(np.degrees(orientation_image[row, col]) % 180)


def extract_minutiae(image_path, output_dir=None, save_steps=False, spurious_thresh=23):
    """Enhance a fingerprint image and extract its minutiae (ridge terminations
    and bifurcations).

    Returns a tuple (minutiae, overlay_image) where `minutiae` is a list of
    dicts: {"type": "end"|"bif", "row": int, "col": int, "angle_deg": float}.
    """
    img = _load_and_resize(image_path)
    enhanced = image_enhance(img, return_all=True)
    binary_img = enhanced["binary"]
    orientation = enhanced["orientation"]

    skel = skimage.morphology.skeletonize(binary_img)
    skel = np.uint8(skel) * 255

    mask = binary_img * 255
    minutiae_term, minutiae_bif = getTerminationBifurcation(skel, mask)

    term_labels = skimage.measure.label(minutiae_term, connectivity=2)
    term_regions = skimage.measure.regionprops(term_labels)
    minutiae_term = removeSpuriousMinutiae(term_regions, np.uint8(binary_img), spurious_thresh)

    bif_labels = skimage.measure.label(minutiae_bif, connectivity=2)
    term_labels = skimage.measure.label(minutiae_term, connectivity=2)

    rows, cols = skel.shape
    overlay = np.zeros((rows, cols, 3), np.uint8)
    overlay[:, :, 0] = skel
    overlay[:, :, 1] = skel
    overlay[:, :, 2] = skel

    minutiae = []
    for region in skimage.measure.regionprops(bif_labels):
        row, col = np.int16(np.round(region.centroid))
        minutiae.append({
            "type": "bif",
            "row": int(row),
            "col": int(col),
            "angle_deg": _minutiae_angle_degrees(orientation, row, col),
        })
        rr, cc = skimage.draw.circle_perimeter(row, col, 3, shape=overlay.shape[:2])
        skimage.draw.set_color(overlay, (rr, cc), (255, 0, 0))

    for region in skimage.measure.regionprops(term_labels):
        row, col = np.int16(np.round(region.centroid))
        minutiae.append({
            "type": "end",
            "row": int(row),
            "col": int(col),
            "angle_deg": _minutiae_angle_degrees(orientation, row, col),
        })
        rr, cc = skimage.draw.circle_perimeter(row, col, 3, shape=overlay.shape[:2])
        skimage.draw.set_color(overlay, (rr, cc), (0, 0, 255))

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(str(output_dir / "enhanced.bmp"), np.uint8(binary_img) * 255)
        cv2.imwrite(str(output_dir / "Minutiae.bmp"), overlay)

        with open(output_dir / "minutiae.txt", "w") as f:
            for m in minutiae:
                f.write(f"{m['type']}\t{m['row']} {m['col']}\t{m['angle_deg']:.1f}\n")

        if save_steps:
            steps_dir = output_dir / "steps" / Path(image_path).stem
            steps_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(steps_dir / "1_normalized.png"), _normalize_to_uint8(enhanced["normalized"]))
            cv2.imwrite(str(steps_dir / "2_orientation.png"), _normalize_to_uint8(orientation % np.pi))
            cv2.imwrite(str(steps_dir / "3_filtered.png"), _normalize_to_uint8(enhanced["filtered"]))
            cv2.imwrite(str(steps_dir / "4_skeleton.png"), skel)
            cv2.imwrite(str(steps_dir / "5_minutiae.png"), overlay)

    return minutiae, overlay


def _parse_args():
    parser = argparse.ArgumentParser(description="Extract minutiae from a fingerprint image.")
    parser.add_argument("image", nargs="?", default=str(DEFAULT_IMAGE), help="Path to the input fingerprint image.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Where to write enhanced.bmp, Minutiae.bmp and minutiae.txt.")
    parser.add_argument("--save-steps", action="store_true", help="Also save intermediate pipeline images (normalized, orientation, filtered, skeleton).")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    minutiae, _ = extract_minutiae(args.image, output_dir=args.output_dir, save_steps=args.save_steps)
    term_count = sum(1 for m in minutiae if m["type"] == "end")
    bif_count = sum(1 for m in minutiae if m["type"] == "bif")
    print(f"Found {term_count} terminations and {bif_count} bifurcations.")
    print(f"Results written to {args.output_dir}")

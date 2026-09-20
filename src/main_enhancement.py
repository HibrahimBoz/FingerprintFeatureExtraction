# -*- coding: utf-8 -*-
"""
CLI: enhance a fingerprint image and extract its minutiae.

This uses the official, actively maintained packages that the original
author (Utkarsh-Deshmukh) later split this project's algorithm into,
rather than a vendored, aging copy of the same code:
- https://pypi.org/project/fingerprint-enhancer/
- https://pypi.org/project/fingerprint-feature-extractor/
"""

import argparse
from pathlib import Path

import cv2
import fingerprint_enhancer
import fingerprint_feature_extractor
import numpy as np
import skimage.draw

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IMAGE = PROJECT_ROOT / "images" / "parmak izi 1.bmp"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "enhanced"


def _draw_overlay(base_img, terminations, bifurcations):
    rows, cols = base_img.shape
    overlay = np.zeros((rows, cols, 3), np.uint8)
    for channel in range(3):
        overlay[:, :, channel] = base_img

    for m in terminations:
        rr, cc = skimage.draw.circle_perimeter(m.locX, m.locY, 3, shape=overlay.shape[:2])
        skimage.draw.set_color(overlay, (rr, cc), (0, 0, 255))
    for m in bifurcations:
        rr, cc = skimage.draw.circle_perimeter(m.locX, m.locY, 3, shape=overlay.shape[:2])
        skimage.draw.set_color(overlay, (rr, cc), (255, 0, 0))
    return overlay


def extract_minutiae(image_path, output_dir=None, spurious_minutiae_thresh=10):
    """Enhance a fingerprint image and extract its minutiae.

    Returns (terminations, bifurcations, enhanced_img). Each minutia is a
    fingerprint_feature_extractor.MinutiaeFeature: .locX/.locY (row/col),
    .Orientation (list of angles in degrees), .Type ("Termination"/"Bifurcation").
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    enhanced = fingerprint_enhancer.enhance_fingerprint(img, resize=True)
    enhanced_img = np.uint8(enhanced) * 255

    terminations, bifurcations = fingerprint_feature_extractor.extract_minutiae_features(
        enhanced_img,
        spuriousMinutiaeThresh=spurious_minutiae_thresh,
        invertImage=False,
        showResult=False,
        saveResult=False,
    )

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(str(output_dir / "enhanced.bmp"), enhanced_img)
        cv2.imwrite(str(output_dir / "Minutiae.bmp"), _draw_overlay(enhanced_img, terminations, bifurcations))

        with open(output_dir / "minutiae.txt", "w") as f:
            for m in terminations:
                angles = ",".join(f"{a:.1f}" for a in m.Orientation)
                f.write(f"end\t{m.locX} {m.locY}\t{angles}\n")
            for m in bifurcations:
                angles = ",".join(f"{a:.1f}" for a in m.Orientation)
                f.write(f"bif\t{m.locX} {m.locY}\t{angles}\n")

    return terminations, bifurcations, enhanced_img


def _parse_args():
    parser = argparse.ArgumentParser(description="Extract minutiae from a fingerprint image.")
    parser.add_argument("image", nargs="?", default=str(DEFAULT_IMAGE), help="Path to the input fingerprint image.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Where to write enhanced.bmp, Minutiae.bmp and minutiae.txt.")
    parser.add_argument("--spurious-thresh", type=float, default=10, help="Minimum distance (px) between minutiae; closer ones are dropped as noise.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    terminations, bifurcations, _ = extract_minutiae(
        args.image, output_dir=args.output_dir, spurious_minutiae_thresh=args.spurious_thresh
    )
    print(f"Found {len(terminations)} terminations and {len(bifurcations)} bifurcations.")
    print(f"Results written to {args.output_dir}")

# -*- coding: utf-8 -*-
"""
Simplified minutiae-based fingerprint comparison.

This is a teaching/demo matcher, not a production biometric matcher: it
assumes both images are already roughly aligned (same finger position,
rotation and scale) and compares minutiae by raw pixel distance and ridge
angle only. A real matcher would first register the two minutiae sets
(e.g. via Hough-transform or RANSAC alignment) to be rotation/translation
invariant.
"""

import argparse
import math

from main_enhancement import extract_minutiae


def match_minutiae(minutiae_a, minutiae_b, distance_threshold=15, angle_threshold_deg=20):
    """Greedily pairs minutiae of the same type between two sets.

    Returns the list of matched (index_a, index_b, distance) triples.
    """
    used_b = set()
    matches = []
    for i, ma in enumerate(minutiae_a):
        best_j, best_dist = None, None
        for j, mb in enumerate(minutiae_b):
            if j in used_b or ma["type"] != mb["type"]:
                continue
            dist = math.hypot(ma["row"] - mb["row"], ma["col"] - mb["col"])
            if dist > distance_threshold:
                continue
            angle_diff = abs(ma["angle_deg"] - mb["angle_deg"]) % 180
            angle_diff = min(angle_diff, 180 - angle_diff)
            if angle_diff > angle_threshold_deg:
                continue
            if best_dist is None or dist < best_dist:
                best_dist, best_j = dist, j
        if best_j is not None:
            used_b.add(best_j)
            matches.append((i, best_j, best_dist))
    return matches


def similarity_score(minutiae_a, minutiae_b, matches):
    denom = max(len(minutiae_a), len(minutiae_b), 1)
    return len(matches) / denom


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_a", help="Path to the first fingerprint image.")
    parser.add_argument("image_b", help="Path to the second fingerprint image.")
    parser.add_argument("--distance-threshold", type=float, default=15, help="Max pixel distance between matched minutiae.")
    parser.add_argument("--angle-threshold", type=float, default=20, help="Max ridge angle difference (degrees) between matched minutiae.")
    parser.add_argument("--match-score-threshold", type=float, default=0.3, help="Similarity score above which the two images are declared a match.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    minutiae_a, _ = extract_minutiae(args.image_a)
    minutiae_b, _ = extract_minutiae(args.image_b)

    matches = match_minutiae(minutiae_a, minutiae_b, args.distance_threshold, args.angle_threshold)
    score = similarity_score(minutiae_a, minutiae_b, matches)

    print(f"Image A: {len(minutiae_a)} minutiae")
    print(f"Image B: {len(minutiae_b)} minutiae")
    print(f"Matched: {len(matches)} minutiae pairs")
    print(f"Similarity score: {score:.2f}")
    verdict = "SAME finger (likely)" if score >= args.match_score_threshold else "DIFFERENT fingers (likely)"
    print(f"Verdict (threshold {args.match_score_threshold}): {verdict}")

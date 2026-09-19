# FingerprintFeatureExtraction

Extracts minutiae features — ridge terminations and bifurcations, each with
its ridge angle — from a fingerprint image. The image is first enhanced
with an oriented Gabor filter bank (ridge orientation decides the filter
orientation), then skeletonized, then scanned for minutiae.

![minutiae example](https://user-images.githubusercontent.com/13918778/35665327-9ddbd220-06da-11e8-8fa9-1f5444ee2036.png)

This project builds on
[Fingerprint-Enhancement-Python](https://github.com/Utkarsh-Deshmukh/Fingerprint-Enhancement-Python),
which implements the enhancement algorithm from:

> Hong, L., Wan, Y., and Jain, A. K. "Fingerprint image enhancement:
> Algorithm and performance evaluation." IEEE Transactions on Pattern
> Analysis and Machine Intelligence 20, 8 (1998), pp 777-789.

The enhancement code is itself a Python port of Dr. Peter Kovesi's original
MATLAB implementation.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Extract minutiae from one image

```bash
cd src
python main_enhancement.py                      # uses the sample image in images/
python main_enhancement.py path/to/image.bmp     # or your own image
python main_enhancement.py path/to/image.bmp --save-steps   # also dump intermediate pipeline images
```

Output is written to `enhanced/`:
- `enhanced.bmp` — the enhanced, binarized fingerprint
- `Minutiae.bmp` — the skeleton with terminations (blue) and bifurcations (red) circled
- `minutiae.txt` — one line per minutia: `type<TAB>row col<TAB>angle_degrees`
- with `--save-steps`, `steps/<image_name>/` also gets the normalized, orientation, filtered and skeleton images for inspection/presentation

### Compare two fingerprints

```bash
cd src
python match_fingerprints.py imageA.bmp imageB.bmp
```

This is a simplified, teaching-purpose matcher: it pairs minutiae between
the two images by pixel distance and ridge angle, assuming the two
fingerprints are already roughly aligned (no rotation/translation
registration is performed). It reports a similarity score and a same/
different verdict. It is meant to illustrate the matching concept, not to
be a production-grade biometric matcher.

## Project layout

```
images/          sample input fingerprint image(s)
enhanced/        output of main_enhancement.py (generated, not needed in git)
src/
  ridge_segment.py, ridge_orient.py, ridge_freq.py, frequest.py,
  ridge_filter.py, image_enhance.py    -- Gabor-filter based enhancement
  getTerminationBifurcation.py         -- minutiae detection on the skeleton
  removeSpuriousMinutiae.py            -- drops minutiae that are too close together
  main_enhancement.py                  -- CLI: enhance + extract minutiae
  match_fingerprints.py                -- CLI: compare two fingerprints
```

## License

BSD 2-Clause — see [LICENSE](LICENSE). Enhancement algorithm and original
implementation by Utkarsh Deshmukh / Peter Kovesi; minutiae extraction,
angle computation and matching demo added on top of it.

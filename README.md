# DualFisheyeStitcher

`DualFisheyeStitcher` is a Python class designed to perform fast panoramic stitching from two circular fisheye camera inputs (e.g., Ricoh Theta Z1). It includes fisheye correction (dewarping) using precomputed lookup tables and stitching based on overlapping regions.

## Class Overview

This class handles:

* Precomputing dewarping LUTs (lookup tables)
* Applying fast equirectangular projection
* Merging both corrected fisheye frames into a panoramic frame

## Constructor

### Parameters:

* `fov`: Field of view of the fisheye camera in degrees (typically \~190°).
* `frame_width`: Width of the input fisheye images.
* `frame_height`: Height of the input fisheye images.

### Initializes:

* Overlap percentage based on camera FOV.
* Precomputed dewarping lookup tables (`map_x`, `map_y`).
* Output dimensions for undistorted frames.

## calculate\_overlapping\_region()

Calculates the horizontal overlapping percentage between the two 180°-spaced fisheye cameras:

* Computes:
  `overlap_angle = 2 * FOV - 360`
* Converts to a ratio over the full 2×FOV span.
* Example: FOV = 190 → 20° overlap → ≈5.3%.

## precompute\_dewarp\_lut(frame\_width, frame\_height, frame\_fov)

Generates remapping lookup tables (`map_x`, `map_y`) to convert circular fisheye images into an equirectangular format.

* Uses equidistant projection model.
* Precomputes the transformation for performance.
* Outputs remap matrices used by OpenCV’s `cv2.remap()`.

## fast\_equirectangular\_dewarping(frame)

Applies the precomputed LUTs to undistort a fisheye frame efficiently.

* Internally uses `cv2.remap(...)`.
* Very fast (real-time capable).
* Returns the undistorted (equirectangular) image.

## stitch\_by\_shift(left\_frame, right\_frame)

Performs the panoramic stitching of two undistorted images by:

1. Splitting left and right frames into:

   * Main region (non-overlapping)
   * Overlapping region
2. Blending the overlapping zones using a linear alpha mask.
3. Concatenating the resulting parts.

## stitch\_frames(left\_frame, right\_frame)

High-level method that:

* Applies fast dewarping to both inputs.
* Stitches them using `stitch_by_shift(...)`.
* Returns the final panoramic output.

## Example Usage

```python
stitcher = DualFisheyeStitcher(fov=190, frame_width=960, frame_height=960)
panorama = stitcher.stitch_frames(left_img, right_img)
```

<div align="center">
  <img src="readme_images/demo_stitching.gif" alt="Single-Object-Tracking" width="650">
</div>



## Notes

* The camera's field of view (FOV) must be greater than 180° to ensure sufficient overlap between the two fisheye images.
* Assumes cameras are aligned horizontally with minimal tilt.
* Overlap zone blending is linear; can be extended to multiband blending if needed.
* The code is optimized for real-time processing and achieves between 29–30 FPS under typical conditions using precomputed LUTs.

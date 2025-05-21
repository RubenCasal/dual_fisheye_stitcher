import cv2
import numpy as np

class DualFisheyeStitcher:
    def __init__(self, fov, frame_width, frame_height):
    
        self.fov = fov

        # Shape of the raw fisheye frames
        self.frame_width = frame_width
        self.frame_height = frame_height

        # Calculate overlap percentage
        self.overlap_percentage = self.calculate_overlapping_region()

        # Precompute dewarping lookup tables (LUTs)
        self.map_x, self.map_y = self.precompute_dewarp_lut(self.frame_width, self.frame_height, self.fov)

        # Shape of the dewarped frames
        self.dewarped_height, self.dewarped_width = self.map_y.shape

    def calculate_overlapping_region(self):
        # Assuming the 2 cameras are placed 180 degrees from each other

        # Calculate the overlap angle
        overlap_angle = 2 * self.fov - 360

        # Convert to overlap percentage
        overlap_percentage = overlap_angle / (2 * self.fov) # Corrected calculation

        return overlap_percentage # Return the calculated percentage

    def stitch_by_shift(self, left_frame, right_frame):
        # Overlapping in the horizontal section
        overlap = int(self.dewarped_width * self.overlap_percentage)

        # Crop frames
        left_main = left_frame[:, :self.dewarped_width - overlap]
        right_main = right_frame[:, overlap:]
        left_overlap = left_frame[:, self.dewarped_width - overlap:]
        right_overlap = right_frame[:, :overlap]

        # merge in the overlapping zone
        alpha = np.linspace(1, 0, overlap).reshape(1, -1, 1)
        blended = (left_overlap * alpha + right_overlap * (1 - alpha)).astype(np.uint8)

        # Concatenate frames
        result = np.concatenate([left_main, blended, right_main], axis=1)

        return result

    def precompute_dewarp_lut(self, frame_width, frame_height, frame_fov):
        out_w = frame_width
        out_h = frame_height // 2 # Common for 180-degree vertical output for fisheye

        fov_rad = np.radians(frame_fov)

        theta = np.linspace(-np.pi / 2, np.pi / 2, out_w)
        phi = np.linspace(-np.radians(60), np.radians(60), out_h) # Adjusted vertical range
        theta, phi = np.meshgrid(theta, phi)

        dx = np.cos(phi) * np.sin(theta)
        dy = np.sin(phi)
        dz = np.cos(phi) * np.cos(theta)

        angle = np.arccos(dz)
        f = frame_width / fov_rad
        r = f * angle

        eps = 1e-8
        norm = np.sqrt(dx**2 + dy**2) + eps

        map_x = (dx / norm) * r + frame_width/2
        map_y = (dy / norm) * r + frame_height/2

        return map_x.astype(np.float32), map_y.astype(np.float32)

    def fast_equirectangular_dewarping(self, frame):
        # Uses the precomputed map_x and map_y
        return cv2.remap(frame, self.map_x, self.map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)



    def stitch_frames(self, left_frame, right_frame):
        #  Fast dewarp with LUTs (Parallelized)
        
        undist_left = self.fast_equirectangular_dewarping(left_frame)
        undist_right = self.fast_equirectangular_dewarping(right_frame)


        
        # stich undistorted images
        stitched = self.stitch_by_shift(undist_left, undist_right)
     
        return stitched
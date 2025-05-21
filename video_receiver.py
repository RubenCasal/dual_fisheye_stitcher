import cv2
import zmq
import numpy as np
import time

from dual_fisheye_stitcher import DualFisheyeStitcher 

FRAME_WIDTH = 960
FRAME_HEIGHT = 960
FOV = 190

COSTLY_OPERATION_ITERATIONS = 100000  # Adjust to simulate heavy computation

def perform_costly_operation():
    """Simulates a computationally expensive operation."""
    result = 0.0
    for i in range(COSTLY_OPERATION_ITERATIONS):
        result += np.sin(i * 0.001) * np.cos(i * 0.002)
    return result

context = zmq.Context()
sub_left = context.socket(zmq.SUB)
sub_left.connect("tcp://localhost:5555")
sub_left.setsockopt(zmq.SUBSCRIBE, b"")
sub_left.setsockopt(zmq.RCVHWM, 1)

sub_right = context.socket(zmq.SUB)
sub_right.connect("tcp://localhost:5556")
sub_right.setsockopt(zmq.SUBSCRIBE, b"")
sub_right.setsockopt(zmq.RCVHWM, 1)

K = np.array([
    [FRAME_WIDTH / 2, 0, FRAME_WIDTH / 2],
    [0, FRAME_HEIGHT / 2, FRAME_HEIGHT / 2],
    [0, 0, 1]
])

stitcher = DualFisheyeStitcher(FOV, FRAME_WIDTH, FRAME_HEIGHT, K)
OVERLAP = stitcher.overlap_percentage
print(OVERLAP)

cv2.namedWindow("Panoramic Stitch", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Panoramic Stitch", 1280, 480)

fps_counter = 0
start_time = time.time()
total_stitch_time = 0
frame_count_for_avg = 0

while True:
    try:
        try:
            jpg_left = sub_left.recv(flags=zmq.NOBLOCK)
        except zmq.Again:
            jpg_left = None

        try:
            jpg_right = sub_right.recv(flags=zmq.NOBLOCK)
        except zmq.Again:
            jpg_right = None

        left = cv2.imdecode(np.frombuffer(jpg_left, dtype=np.uint8), cv2.IMREAD_COLOR) if jpg_left else None
        right = cv2.imdecode(np.frombuffer(jpg_right, dtype=np.uint8), cv2.IMREAD_COLOR) if jpg_right else None

        if left is None or right is None:
            time.sleep(0.001)
            continue

        # perform_costly_operation()  # Optional simulation

        stitch_start_time = time.perf_counter()
        stitched = stitcher.stitch_frames(left, right)        
        stitch_end_time = time.perf_counter()

        stitch_duration = stitch_end_time - stitch_start_time
        total_stitch_time += stitch_duration
        frame_count_for_avg += 1

        cv2.imshow("Panoramic Stitch", stitched)

        fps_counter += 1
        if time.time() - start_time >= 1.0:
            avg_stitch_time_ms = (total_stitch_time / frame_count_for_avg) * 1000 if frame_count_for_avg > 0 else 0
            print(f"Stitching FPS: {fps_counter:.2f} | Avg Stitch Time: {avg_stitch_time_ms:.2f} ms")
            fps_counter = 0
            total_stitch_time = 0
            frame_count_for_avg = 0
            start_time = time.time()

        if cv2.waitKey(1) & 0xFF == 27:
            break

    except KeyboardInterrupt:
        break

cv2.destroyAllWindows()

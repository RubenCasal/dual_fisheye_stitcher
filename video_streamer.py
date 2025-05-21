import cv2
import zmq
import time

# ZeroMQ setup
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")
socket2 = context.socket(zmq.PUB)
socket2.bind("tcp://*:5556")

# Video input
cap_left = cv2.VideoCapture("ricoh_left2.mp4")
cap_right = cv2.VideoCapture("ricoh_right2.mp4")

# Visualization windows
cv2.namedWindow("Left Stream", cv2.WINDOW_NORMAL)
cv2.namedWindow("Right Stream", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Left Stream", 640, 640)
cv2.resizeWindow("Right Stream", 640, 640)

# FPS monitoring
frame_counter = 0
start_second = time.time()
frame_time_target = 1.0 / 30.0  # target ~30 FPS

# Resize dimensions (square)
target_size = (960, 960)

while True:
    frame_start = time.time()

    ret_l, left = cap_left.read()
    ret_r, right = cap_right.read()

    if not (ret_l and ret_r):
        cap_left.set(cv2.CAP_PROP_POS_FRAMES, 0)
        cap_right.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # Resize to square for transmission
    left_resized = cv2.resize(left, target_size)
    right_resized = cv2.resize(right, target_size)

    # Show preview in smaller windows
    cv2.imshow("Left Stream", cv2.resize(left_resized, (640, 640)))
    cv2.imshow("Right Stream", cv2.resize(right_resized, (640, 640)))

    # Encode and transmit
    _, buf_left = cv2.imencode('.jpg', left_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    _, buf_right = cv2.imencode('.jpg', right_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

    socket.send(buf_left.tobytes())
    socket2.send(buf_right.tobytes())

    # Track FPS
    frame_counter += 1
    if time.time() - start_second >= 1.0:
        print(f"📡 Real transmission: {frame_counter} FPS")
        frame_counter = 0
        start_second = time.time()

    if cv2.waitKey(1) & 0xFF == 27:
        break

    # Enforce 30 FPS cap
    elapsed = time.time() - frame_start
    if elapsed < frame_time_target:
        time.sleep(frame_time_target - elapsed)

cap_left.release()
cap_right.release()
cv2.destroyAllWindows()

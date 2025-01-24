import cv2
import imutils
import time
import requests
import os
from datetime import datetime
from decouple import config

# Load the server URL from environment variables
DATABASE_SERVER_URL = config("DATABASE_SERVER_URL", default="http://localhost:8000/api/Motion_Alarm")


# Directory to store recorded videos
RECORD_DIR = "recorded_videos"
if not os.path.exists(RECORD_DIR):
    os.makedirs(RECORD_DIR)

# Motion detection function
def motion_detection():
    capture = cv2.VideoCapture(0)
    capture.set(3, 800)  
    capture.set(4, 550)  
    first_frame = None
    recording = False
    out = None

    while True:
        ret, frame = capture.read()
        if not ret:
            break
        # Resize and preprocess frame
        frame = imutils.resize(frame, width=500)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

        if first_frame is None:
            first_frame = gray_frame
            continue

        # Compute frame difference
        frame_diff = cv2.absdiff(first_frame, gray_frame)
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        motion_detected = False

        for contour in contours:
            if cv2.contourArea(contour) < 500:  
                continue

            motion_detected = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Start or stop recording based on motion detection
        if motion_detected and not recording:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = os.path.join(RECORD_DIR, f"motion_{timestamp}.avi")
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            out = cv2.VideoWriter(video_path, fourcc, 20.0, (frame.shape[1], frame.shape[0]))
            recording = True

        if recording:
            out.write(frame)
            if not motion_detected:
                # Stop recording if no motion is detected
                out.release()
                out = None
                recording = False

                # Posting Function call
                post_motion_event(video_path)

        cv2.imshow("Motion Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    capture.release()
    if out:
        out.release()
    cv2.destroyAllWindows()

# Post motion events to the remote database server
def post_motion_event(video_path):
    try:
        with open(video_path, "rb") as video_file:
            files = {"file": video_file}
            response = requests.post(DATABASE_SERVER_URL, files=files)

            if response.status_code == 200:
                print("Successfully posted motion event.")
            else:
                print(f"Failed to post motion event: {response.status_code}")
    except Exception as e:
        print(f"Error posting motion event: {e}")

if __name__ == "__main__":
    motion_detection()

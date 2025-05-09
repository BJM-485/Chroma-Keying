import cv2
import numpy as np

video_cap = cv2.VideoCapture('green screen-asteroid.mp4')
if not video_cap.isOpened():
    print('Error: cannot open the video file.')
    exit()

ret_val, frame = video_cap.read()
user_data = {'vertex1': None,
             'vertex2': None,
             'green_screen': None,
             'tolerance': 1.5}

windowName = 'Select Green Screen and Tolerance'
cv2.namedWindow(winname=windowName)

def select_green_screen(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        param['vertex1'] = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        param['vertex2'] = (x, y)
        x1, y1 = param['vertex1']
        x2, y2 = param['vertex2']
        param['green_screen'] = frame[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)].copy()
        cv2.destroyWindow(windowName)

cv2.setMouseCallback(windowName, select_green_screen, param=user_data)

def update_tolerance(value, param):
    param['tolerance'] = value / 100.0

# In OpenCV, trackbars only work with integers, but tolerance values require decimal precision.
cv2.createTrackbar('Tolerance', windowName, 150, 300, lambda x: update_tolerance(x, user_data))

while user_data['green_screen'] is None:
    cv2.imshow(winname=windowName, mat=frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        video_cap.release()
        cv2.destroyAllWindows()
        exit()

green_screen_hsv = cv2.cvtColor(src=user_data['green_screen'], code=cv2.COLOR_BGR2HSV)
mean_hsv = np.mean(green_screen_hsv, axis=(0, 1))
std_hsv = np.std(green_screen_hsv, axis=(0, 1))

lower_green = np.clip(mean_hsv - user_data['tolerance'] * std_hsv, 0, 255).astype(np.uint8)
upper_green = np.clip(mean_hsv + user_data['tolerance'] * std_hsv, 0, 255).astype(np.uint8)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
output_video = cv2.VideoWriter('output.mp4', fourcc, 30.0, (frame.shape[1], frame.shape[0]))

video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

while video_cap.isOpened():
    ret, frame = video_cap.read()
    if not ret:
        break
    frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(frame_hsv, lower_green, upper_green)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    background = cv2.imread('space.jpg', cv2.IMREAD_COLOR)
    background = cv2.resize(background, (frame_hsv.shape[1], frame_hsv.shape[0]))

    foreground = cv2.bitwise_and(frame, frame, mask=~mask)
    background = cv2.bitwise_and(background, background, mask=mask)
    result = cv2.add(foreground, background)

    cv2.imshow('Result', result)
    output_video.write(result)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

video_cap.release()
output_video.release()
cv2.destroyAllWindows()
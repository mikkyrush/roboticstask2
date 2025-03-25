import cv2
import pytesseract
import numpy as np
from PIL import ImageGrab
from datetime import datetime

carpark = {}
#ensure image is in suitable format
def image_capture(bbox=(300, 300, 1500, 1000)):
    img_cam = np.array(ImageGrab.grab(bbox))
    img_cam = cv2.cvtColor(img_cam, cv2.COLOR_RGB2BGR)
    return img_cam

#camera setup
cam = cv2.VideoCapture(0)
cam.set(3,640)
cam.set(4,480)

#begin streaming
while True:
    print("Reading from Camera")
    ret, frame = cam.read()
#make grayscale
    gray_scale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ret, binary_img = cv2.threshold(gray_scale, 120, 255, cv2.THRESH_BINARY) 
    
#text detection per-frame
    print("Text Detection")
    text_detection = pytesseract.image_to_string(binary_img)


# display text and store in dictionary
    text_detection = text_detection.strip()
    if text_detection:
        print('Text:', text_detection)
        carpark[text_detection] = datetime.now
    cv2.imshow("OCR", binary_img)


    if cv2.waitKey(1) == ord('e'):
        break
print(carpark)
cam.release()
cv2.destroyAllWindows()	

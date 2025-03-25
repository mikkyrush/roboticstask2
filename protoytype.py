import cv2
import pytesseract
import numpy as np
from PIL import ImageGrab
from datetime import datetime
from gpiozero import AngularServo
from gpiozero import DistanceSensor
from time import sleep


payment_log = {}
carpark = {}


def gateopen():
    # Initialise Servo
    servo = AngularServo(17, min_pulse_width=0.0006, max_pulse_width=0.0023)

    # Initialise ultrasonic sensor
    sensor = DistanceSensor(trigger=23, echo=24)


    print("Servo: Default State Gate Closed")
    servo.angle = 90
    sleep(2)
    print("Servo: Open Gate")
    servo.angle = 0

    carpassedgate = False
    cardetected = False

    while(not carpassedgate):
        sleep(2)
        distance = sensor.distance * 100
        print("Ultrasonic: Distance Detected {} cm".format(distance))
        if(distance < 10):
            print("Ultrasonic: Object detected < 10 cm")
            cardetected = True
        elif(distance > 10 and cardetected):
            print("Ultrasonic: Object no longer detected < 10 cm")
            carpassedgate = True

    print("Servo: Close Gate")
    servo.angle = 90
    sleep(1)

def requestpayment(duration):
    print('Payment Gateway:',' Payment for duration',duration)
    payment_log[datetime.now()] = duration
    return True



#camera setup
cam = cv2.VideoCapture(0)
cam.set(3,640)
cam.set(4,480)

#begin streaming
while True:
    print("Carparks taken: {}".format(len(carpark)))
    print("Reading from Camera")
    ret, frame = cam.read()

#make grayscale
    gray_scale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ret, binary_img = cv2.threshold(gray_scale, 120, 255, cv2.THRESH_BINARY) 
#text detection per-frame
    text_detection = pytesseract.image_to_string(binary_img)


# display text and store in dictionary
    text_detection = text_detection.strip()
    if text_detection:
        print('Text:', text_detection)
        # determine if car is already in the carpark
        if(text_detection in carpark):
            parked_duration = datetime.now() - carpark[text_detection]
            print('Car',text_detection,': Exiting carpark at',datetime.now())
            print('Car',text_detection,': Duration in carpark',parked_duration)
            print('Car',text_detection,': Entered carpark at',carpark[text_detection])
            if(requestpayment(parked_duration)):
                print('Car',text_detection,': Payment Successful.')
                carpark.pop(text_detection)
            else:
                print('Car',text_detection,': Payment not Successful.')
                print('Car',text_detection,': Require Manual Intervention.')
        else:
            carpark[text_detection] = datetime.now()
            print('Car',text_detection,': Entered carpark at',carpark[text_detection])
        gateopen()


    #cv2.imshow("OCR", binary_img)


    if cv2.waitKey(1) == ord('e'):
        break
    sleep(2)
print(carpark)
cam.release()
cv2.destroyAllWindows()	

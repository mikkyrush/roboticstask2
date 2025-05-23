import cv2
import re
import pytesseract
import numpy as np
from PIL import ImageGrab
import RPi.GPIO as GPIO
from datetime import datetime
from gpiozero import AngularServo
from gpiozero import DistanceSensor
from RPLCD.i2c import CharLCD
from time import sleep
from mfrc522 import SimpleMFRC522


import ecies
import sys
import socket
import threading
import binascii

HEADER = 64
PORT = 50512
FORMAT = "utf-8"
DCMSG = "DISCONNECT"
publicKey = b""

#SERVER = "10.1.1.52"
#SERVER = '10.76.95.177'
SERVER = "127.0.0.1"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))


server_Error = {'ERROR0': 'Incorrect Pin','ERROR1': 'Insufficent balance','ERROR2':'Invalid user','ERROR3':'Registered Already','ERROR4':'Invalid Authcode'}
paymentResult = ""


payment_log = {}
carpark = {}

def lcd():
   
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)
    lcd.clear()
    lcd.write_string('Occupied')
    sleep(3)
    lcd.clear()
    lcd.write_string(parkstaken)

def lcdtime():
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)
    lcd.clear()
    lcd.write_string('Time')
    sleep(3)
    lcd.write_string(exittime)
    
  
def lcddisplay(display):
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)
    lcd.clear()
    lcd.write_string(display)

def gateopen():
    sleep(2)
    # Initialise Servo
    servo = AngularServo(18, min_pulse_width=0.0006, max_pulse_width=0.0023)

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




# Function for recieving and decoding messages
def receiveMsgs(client):
    global connected, publicKey, paymentResult
    while True:
        msgLength = client.recv(HEADER).decode(FORMAT)
        if msgLength != "":
            msgLength = int(msgLength)
            msg = client.recv(msgLength).decode(FORMAT)
            print('Message received from',SERVER,':', msg)
            if msg == "DISCONNECTED":
                connected = False
                sys.exit("Disconnected from server.")
            msgArgs = msg.split(":")
            if msgArgs[0] == "PUBLICKEY":
                publicKey = binascii.unhexlify(msgArgs[1])
            else:
                paymentResult = msg
        else:
            break

#Function for sending and encoding data
def send(client, msg):
    if publicKey == b"":
        print("[ERROR] Key is empty (Key has not been received).")
    else:
        encodedMsg = ecies.encrypt(publicKey, msg.encode("utf-8"))

        msgLength = f"{len(encodedMsg):<{HEADER}}".encode(FORMAT)
        client.send(msgLength)
        client.send(encodedMsg)


def requestpayment(duration):
    reader = SimpleMFRC522()

    print('Card Reader: reading')
    id, text = reader.read()
    print(id)
    print(text)
    text = text.strip()
    print('Payment Gateway:',' Payment for duration',duration)
    send(client,f"TRYCHARGE:{id}:{text}:5")
    sleep(1)
    if(paymentResult == 'TRUE'):
        payment_log[datetime.now()] = duration
        return True
    else:
        print('Payment Gateway:',' Error ',server_Error[paymentResult])
        return False

def detect_plate_number():
    # Load the image
   
    #cam = cv2.VideoCapture(0)
    #cam.set(3,640)
    #cam.set(4,480)

    ret, frame = cam.read()

    #cv2.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    #cv2.axis('off')
    #cv2.show()

    brightness = 8

    contrast = 2.3  
    #adjust = cv2.addWeighted(frame, contrast, np.zeros(frame.shape, frame.dtype), 0, brightness)
    adjust = frame
    gray_scale = cv2.cvtColor(adjust, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_scale, (5, 5), 0)
    edges = cv2.Canny(blurred, 100, 200)
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    plate_contour = None
    for contour in contours:     
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)       
        if len(approx) == 4:
            plate_contour = approx
            break

    if plate_contour is not None:
   
        x, y, w, h = cv2.boundingRect(plate_contour)
        plate_image = gray_scale[y:y + h, x:x + w]
        _, thresh = cv2.threshold(plate_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        plate_number = pytesseract.image_to_string(thresh, config='--psm 8 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')  # Treat it as a single word

        return plate_number.strip()
    else:
        return ''



receiver = threading.Thread(target=receiveMsgs, args=[client])
receiver.start()



#camera setup
cam = cv2.VideoCapture(0)
cam.set(3,640)
cam.set(4,480)


plateread = {}
camread = 0

#begin streaming
while True:
    print("Carparks taken: {}".format(len(carpark)))
    parkstaken = format(len(carpark))
    parkstaken = str(parkstaken)
    lcddisplay("Occupied: {}".format(len(carpark)))
    print("Reading from Camera")

    text_detection = detect_plate_number()

    text_detection = re.sub('[\W_]', '', text_detection)
    print('OCR:',text_detection)
    # display text and store in dictionary
   

    if text_detection:

        if(camread == 0):
            plateread = {}

        if(camread <= 5):
            if(text_detection in plateread):
                plateread[text_detection] = plateread[text_detection] + 1
            else:
                plateread[text_detection] = 0
            camread += 1        
        else: 
            camread = 0
            
            text_detection = list(dict(sorted(plateread.items(), key=lambda item: item[1])))[-1]

            print('Text:', text_detection)
            # determine if car is already in the carpark
            if(text_detection in carpark):
                parked_duration = datetime.now() - carpark[text_detection]
                print('Car',text_detection,': Exiting carpark at',datetime.now())
                exittime = str(datetime.now())
                lcddisplay("Parked For: 20 Cost: $5.00")
                print('Car',text_detection,': Duration in carpark',parked_duration)
            
                #lcd.write_string('Duration', parked_duration)
                print('Car',text_detection,': Entered carpark at',carpark[text_detection])
                if(requestpayment(parked_duration)):
                    print('Car',text_detection,': Payment Successful.')
                    #paymentoutput
                    carpark.pop(text_detection)
                else:
                    print('Car',text_detection,': Payment not Successful.')
                    print('Car',text_detection,': Require Manual Intervention.')
                    #paymentoutput
            else:
                carpark[text_detection] = datetime.now()
                print('Car',text_detection,': Entered carpark at',carpark[text_detection])
                #lcd()
                #lcd.write_string('Entered at', carpark[text_detection] )
            gateopen()


    


    if cv2.waitKey(1) == ord('e'):
        break
    
print(carpark)
cam.release()
cv2.destroyAllWindows()	

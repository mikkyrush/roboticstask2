from gpiozero import AngularServo
from time import sleep

servo = AngularServo(17, min_pulse_width=0.0006, max_pulse_width=0.0023)

print("gate closed")
servo.angle = 90
sleep(2)
print("gate open")
servo.angle = 0
sleep(8)
print("gate closed")
servo.angle = 90
sleep(1)

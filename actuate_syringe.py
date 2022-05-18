import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib
import time

class actuate_syringe:
    def __init__(self):
        self.direction= 19
        self.step = 26
        self.motor = RpiMotorLib.A4988Nema(direction, step, (21,21,21), "DRV8825")

    def actuate(self):
        self.motor.motor_go(True, "Full", 500, .0003, False, .05)

    def clean(self):
        GPIO.cleanup()
# Author @xavier_barneclo
# Automated image based contact angle measuring device code
# Goal is to simply run this script while connected to the camera

from contact_angle import contact_angle
from camera_control import camera_control
from actuate_syringe import actuate_syringe
import time

# global test variables
trials = 5
tpt = 5

# intialize classes/variables
cam = camera_control()
syr = actuate_syringe()

# looping cycle that gets contact angle data
curr_trial = 0
while curr_trial < trials:
    # actuate syringes
    syr.actuate()

    # get pictures
    img = cam.write_picture()

    # compute and save contact angles
    finder = contact_angle(img)
    finder.write_output()

    time.sleep(tpt)

syr.clean()

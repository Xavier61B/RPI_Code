from pypylon import pylon

import cv2
import os

class camera_control:
    def __init__(self):
        # Initalizes camera
        tl_factory = pylon.TlFactory.GetInstance()
        self.camera = pylon.InstantCamera()
        self.camera.Attach(tl_factory.CreateFirstDevice())
        self.camera.ExposureTime.SetValue(3000)

    def write_picture(self):
        camera = self.camera

        # Takes photo from 1 frame
        camera.Open()
        camera.StartGrabbing(1)
        grab = camera.RetrieveResult(2000, pylon.TimeoutHandling_Return)
        if grab.GrabSucceeded():
            img = grab.GetArray()

        files = os.listdir()
        i = 1
        out = "trial " + str(i) + ".bmp"
        while out in files:
            i += 1
            out = "result " + str(i) + ".bmp"
        cv2.imwrite(out,img)
        camera.Close()

        return out
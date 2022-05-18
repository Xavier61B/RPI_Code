# Author @xavier_barneclo
# Automated image based contact angle measuring device code
# Goal is to simply call this class from the raspberry pi

import cv2
import numpy as np
from list import list
import os

class contact_angle:
    WHITE = 255               #white pixel value
    BLACK = 0                 #black pixel value

    # FEEL FREE TO TUNE THESE VALUES TO GET MORE ACCURATE CONTACT ANGLE
    order = 2                 #order of polynomial fit
    d_factor = 10             #factor to calculate number of pixels to run polyfit on
    convergence = 10          #difference in angle to determine model convergence
    divergence = 5            #number of points to try until giving up
    error_flag = 5            #number of pixel offset between pinning points before user is alerted to check image manually

    def __init__(self, i):
        # import image to be processed
        image = cv2.imread(i,0)
        self.row = image.shape[0]
        self.column = image.shape[1]

        # create image to be processed and output image
        self.out = cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        self.proc = self.edge_detect(image)

        # create list of liquid boundary
        bound = self.get_list(self.proc)

        # compute contact angles
        self.get_contact_angle(self.proc, bound)

    # outputs computed information via txt file and images
    def write_output(self):
        blank = self.out
        contact_left = self.contact_left
        contact_right = self.contact_right
        flag = self.flag

        # Writing to txt file
        files = os.listdir()
        if not("results" in files):
            os.mkdir("results")
        os.chdir("results")
        files = os.listdir()

        i = 1
        out = "result " + str(i) + ".bmp"
        while out in files:
            i += 1
            out = "result " + str(i) + ".bmp"

        if "output.txt" in files:
            file = open("output.txt", "a") 
        else:
            file = open("output.txt","w")
            file.write("Trial number, left pinning point contact angle, right pinning point contact angle, flag for error\n")
        file.write(str(i) + "," + str(contact_left) + "," + str(contact_right) + "," + str(flag) + "\n")

        # Output image
        cv2.imwrite(out,blank)

    # detects edges from input image
    def edge_detect(self, image):
        # array to store image with edges drawn
        empty = np.zeros((self.row,self.column,1), np.uint8)

        # apply otsu's method to input image
        otsu_threshold, image_result = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU,)

        # Canny edge detection (using Otsu's thresholds)
        edge = cv2.Canny(image_result, otsu_threshold/2,otsu_threshold)

        # countour detection to connect edges
        contours, hierarchy = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        con = self.max(contours)
        cv2.drawContours(empty, [con], -1, (255,255,255), 1)

        return empty

    # returns double linked-list of boundary of droplet
    def get_list(self, empty):
        column = self.column
        row = self.row
        white = self.WHITE

        # Right and left most edge detection
        lhs = None
        rhs = None
        for i in range(column - 1):
            for q in range(row - 1,0,-1):
                if empty[q][i] == white and not lhs:
                    lhs = [q,i]
                if empty[q][column - 1 - i] == white and not rhs:
                    rhs = [q,column - 1 - i]
            if lhs and rhs:
                break

        # Generate droplet boundary points list
        top = self.find_top(empty,lhs)
        bound = list(self.swap(top))
        a = bound.add(empty,white)
        while a:
            a = bound.add(empty,white)

        self.delta = int(self.distance(rhs,lhs)/self.d_factor)
        
        return bound
    
    # computes contact angle, detects erros, and draws to output image
    def get_contact_angle(self, empty, bound):
        # intialize variables
        num_l = 0
        num_r = 0
        con_l = False
        con_r = False
        lcontact_right = 0
        lcontact_left = 0
        close = False

        # initialize class varialbes for conciseness
        delta = self.delta
        order = self.order
        divergence = self.divergence
        convergence = self.convergence
        error_flag = self.error_flag

        while not close:
            if con_r and con_l:
                close = True
                contact_right = lcontact_right
                contact_left = lcontact_left
                break
            
            corners = cv2.goodFeaturesToTrack(empty, 2, 0.01, 10)
            corners = np.int0(corners)

            c = []
            for i in corners:
                c.append(i.ravel())

            # Find pinning points in boundary list
            lpp = bound.lfind(c[1])
            rpp = bound.rfind(c[0])

            # get points for polyfitting
            le = np.array(bound.get_list(lpp,delta))
            ri = np.array(bound.get_list_back(rpp,delta))

            # Polyfit
            zero_y1 = le[1,0]
            zero_y2 = ri[1,0]
            zero_x1 = le[0,0]
            zero_x2 = ri[0,0]

            lpol = np.poly1d(np.polyfit(le[1,:],le[0,:],order))
            rpol = np.poly1d(np.polyfit(ri[1,:],ri[0,:],order))


            # Find contact angle
            dl = np.polyder(lpol)
            dr = np.polyder(rpol)

            suml = 0
            sumr = 0
            
            for i in range(num_l + 1):
                suml += dl(zero_y1 - i)

            for i in range(num_r + 1):
                sumr += dr(zero_y2 - i)
            
            dl = suml/(num_l + 1)
            dr = sumr/(num_r + 1)

            dely = c[0][1] - c[1][1]
            delx = c[0][0] - c[1][0]
            substrate_angle = np.degrees(np.arctan2(-1 * dely,delx))

            contact_right = 180 - np.degrees(np.arctan2(1,-1*dr)) + substrate_angle
            contact_left = np.degrees(np.arctan2(1,-1*dl)) - substrate_angle

            if num_l + num_r > divergence:
                print("Solution diverges, shape is too rough for proper pinning point detection")
                break
            
            if abs(contact_right - lcontact_right) < convergence:
                con_r = True
            else:
                num_r += 1

            if abs(contact_left - lcontact_left) < convergence:
                con_l = True
            else:
                num_l += 1

            lcontact_right = contact_right
            lcontact_left = contact_left

        # define outputs
        self.contact_right = contact_right
        self.contact_left = contact_left

        self.flag = False
        if error_flag < abs(c[1][1] - c[0][1]):
            self.flag = True
            print("Warning, large pinning point deviation observed")

        # Draw to output image
        a = bound.start.next
        for i in range(bound.get_size()-1):
            x = a.get_x()
            y = a.get_y()
            self.out[y,x] = [0,255,255]
            a = a.get_next()

        self.out = self.draw(zero_x1,zero_y1,self.out,dl,delta)
        self.out = self.draw(zero_x2,zero_y2,self.out,dr,delta)

    ## HELPER FUNCTIONS ##

    # Distance function for points
    def distance(self, p_0,p_1):
        return ((p_0[1]-p_1[1])**2+(p_0[0]-p_1[0])**2)**.5

    def find_top(self, img, lhs):
        row = lhs[0]
        for i in range(row,0,-1):
            cond = False
            for q in range(0,img.shape[1]):
                if img[i][q] == 255:
                    cond = True
            if not cond:
                for q in range(0,img.shape[1]):
                    if img[i + 1][q] == 255:
                        return [i+1,q]

    # Drawing helper function
    def draw(self, x_0, y_0, blank, m, d):
        len = int(d*1.5)
        y = y_0
        x = int(m*(y-y_0)+x_0)
        for i in range(len):
            if not ((x >= 0 and x < blank.shape[1]) and (y >= 0 and y < blank.shape[0])):
                break
            blank[y,x] = [255,0,0]
            y -= 1
            x = int(m*(y-y_0)+x_0)
        return blank

    # finds array of max length
    def max(self, c):
        max = np.array([])
        for i in c:
            if i.size > max.size:
                max = i
        return max

    # Swap two indices
    def swap(self, point):
        new = [point[1],point[0]]
        return new
        
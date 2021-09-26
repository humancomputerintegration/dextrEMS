import cv2 
import numpy as np
import datetime

key = cv2. waitKey(1)
webcam = cv2.VideoCapture(1)
webcam.set(3, 1920) # this somehow set resolution to correct ones, not 800 though

while True:
    try:
        check, frame = webcam.read()
        # for HD camera: downscale from 1920x1080
        # frame = cv2.resize(frame,(1280,720))
        # for low res camera: crop a reigon
        # frame = frame[0:720, 0:1280]

        cv2.imshow("Capturing", frame)

        key = cv2.waitKey(1)
        if key == ord('s'): 
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            cv2.imwrite(filename='webcam_img_'+str(timestamp)+'.jpg', img=frame)
            print("Image saved!")

        elif key == ord('q'):
            print("Turning off camera.")
            webcam.release()
            print("Camera off.")
            print("Program ended.")
            cv2.destroyAllWindows()
            break

    except(KeyboardInterrupt):
        print("Turning off camera.")
        webcam.release()
        print("Camera off.")
        print("Program ended.")
        cv2.destroyAllWindows()
        break


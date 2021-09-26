# usage: python annotator.py [user no.]
# this will read all image files in this directory, let you annotate, and save into a csv file

import cv2 
import numpy as np
import glob
import sys

user = sys.argv[1]

mouseX, mouseY = 0, 0
pointIdx = 0
pts = np.array([[0,0], [0,0], [0,0]])
angle = 0

data_labels = ['index mcp', 'index pip', 'middle mcp', 'middle pip', 'ring mcp', 'ring pip', 'pinky mcp', 'pinky pip']
data_index = 0

key = cv2. waitKey(1)

w = 1280
h = 360
frame = np.zeros((h,w,3), np.uint8)
img = np.zeros((h,w,3), np.uint8)

images = glob.glob('*.jpg')

f = open('user_'+user+'_data.csv', 'a')
f.write('user,group,trial,actuated_finger,actuated_joint,measured_finger,measured_joint,angle,img_id\n')
f.flush()

def refresh():
    global frame, img, pointIdx
    pointIdx = 0
    frame = img.copy()
    cv2.rectangle(frame, (5,70), (420, 130), (0, 0, 0), -1)
    cv2.putText(frame,'measure angle of ' + data_labels[data_index] + ' angle: ' + str(angle), (10,90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2, cv2.LINE_AA)
    cv2.putText(frame,'[R] reset [S] save [Q] quit', (10,120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2, cv2.LINE_AA)
    cv2.imshow("image", frame)

def compute_angle(points):
    a = points[0]
    b = points[1]
    c = points[2]
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return round(180-np.degrees(angle),1)

def draw_circle(event,x,y,flags,param):
    global mouseX,mouseY,pointIdx, frame, angle
    if event == cv2.EVENT_LBUTTONDOWN:
        if (pointIdx == 0):
            refresh()
        cv2.circle(frame,(x,y),4,(255,255,255),-1)
        cv2.circle(frame,(x,y),2,(255,0,0),-1)
        mouseX,mouseY = x,y
        # print(mouseX, mouseY)
        pts[pointIdx] = [x,y]
        if (pointIdx == 2):
            angle = compute_angle(pts)
            refresh()
            pointIdx = 0
        else:
            pointIdx += 1

cv2.namedWindow('image')
cv2.setMouseCallback('image',draw_circle)

refresh()

for fname in images:

    # get metadata from filename
    metadata = fname.split('_')
    user_no = metadata[1]
    group = metadata[3]
    trial = metadata[5]
    finger = metadata[7]
    joint = metadata[8]
    img_id = metadata[9]

    img = cv2.imread(fname)
    img = cv2.resize(img,(w,h))
    frame = img.copy()
    # cv2.imshow('img',img)
    # cv2.waitKey(500)
    waiting = True
    refresh()

    while waiting:
        try:
            cv2.imshow("image", frame)

            key = cv2.waitKey(1)
            if key == ord('r'): 
                # # reset image
                refresh()
            if key == ord('s'): 
                measured_joint = data_labels[data_index].split(' ')
                f.write(user_no+','+group+','+trial+','+finger+','+joint+','+measured_joint[0]+','+measured_joint[1]+','+str(angle)+','+str(img_id[:-4])+'\n')
                f.flush()
                data_index += 1
                angle = 0
                if (data_index >= len(data_labels)):
                    data_index = 0
                    waiting = False
                else:
                    refresh()

            
        except(KeyboardInterrupt):
            # print("Turning off camera.")
            # webcam.release()
            # print("Camera off.")
            # print("Program ended.")
            # cv2.destroyAllWindows()
            break
    

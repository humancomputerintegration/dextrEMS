# how to recover:

import cv2 
import sys

calibration_para = sys.argv[1]
original_img = sys.argv[2]

cv_file = cv2.FileStorage(calibration_para, cv2.FILE_STORAGE_READ)
camera_matrix = cv_file.getNode("K").mat()
dist_matrix = cv_file.getNode("D").mat()
cv_file.release()
w = 1920
h = 1080
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(camera_matrix,dist_matrix,(w,h),1,(w,h))

img = cv2.imread(original_img)

# undistort
dst = cv2.undistort(img, camera_matrix, dist_matrix, None, newcameramtx)

# crop the image
# x,y,w,h = roi
# dst = dst[y:y+h, x:x+w]

cv2.imwrite('calibresult.png',dst)

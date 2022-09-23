from rembg import remove
import numpy as np
import cv2
import gc

# input_path = r"C:\Users\HP\Desktop\workspace\Project\FairyTale\Speech2Text2Image\fairytale\testoutput\input\girl-1.jpg"
mask_output_path = r"static\data\mask_image.png"


def bg_remove(data):
    print('remove')
    output = remove(data)
    return output

def create_mask(data):
    print('start generate mask')
    output = bg_remove(data)
    mask = output[:, :, -1]
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGBA)
    cv2.imwrite(mask_output_path, mask)
    gc.collect()
    print('complete')

# example
# write => 저장할 것인지 안할 것인지


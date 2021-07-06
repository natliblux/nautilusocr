import constants.constants as ct
import cv2

# crops all images from image file for a set of blocks related to the same alto file
def get_images(image_path, blocks_stuff):

    image = cv2.imread(image_path)
    if not image is None:
        for block_id in blocks_stuff:
            coords = blocks_stuff[block_id].coordinates
            x = coords[0]
            y = coords[1]
            w = coords[2]
            h = coords[3]
            if x+w > (len(image[0])+ct.IMG_CROP_TOLERANCE) or y+h > (len(image)+ct.IMG_CROP_TOLERANCE):
                print('image coordinates for block ' + block_id + ' are out of bounds in image ' + image_path)
                return
            cropped_image = image[y: y+h, x: x+w]
            blocks_stuff[block_id].image = cropped_image
    else:
        print("couldn't read image at " + image_path)
        return
    return blocks_stuff
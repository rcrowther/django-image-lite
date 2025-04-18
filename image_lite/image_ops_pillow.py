from PIL import Image as PILImage
import math


def photoFX(pillow, anchor):
    if (anchor):
        # break up the tuple of data
        topBottom, leftRight, overlay_path = anchor
        
        # Get the image
        with PILImage.open(overlay_path) as overlay_img:
            # figure from locs the position
            x = 0
            y = 0
            if (topBottom == 'bottom'):
                y = pillow.height - overlay_img.height
            if (leftRight == 'right'):
                x = pillow.width - overlay_img.width                

            # paste over
            pillow.paste(overlay_img, (x, y))
            
            # ditch overlay data (now self-closing? R.C.)
            # overlay_img.close()
    return pillow
    

def resize_force(pillow, width, height):
    '''
    Resize if the image is too big.
    Force to given size, stretching/squeezing the image as 
    appropriate.
    '''
    return pillow.resize((width, height))
    
        
# Sriink only resize. Currently unused. R.C.        
# def resize_aspect_2(pillow, width, height):
    # '''
    # Resize if the image is too big, preserving aspect ratio.
    # Will not resize if dimensions match or are less than the source.
    # @return an image within the given dimensions. The image is usually 
    # smaller in one dimension than the given space.
    # '''
    # s = pillow.size
    # current_width = s[0]
    # current_height = s[1]
    # width_reduce = current_width - width
    # height_reduce = current_height - height
    # if (width_reduce > height_reduce and width_reduce > 0):
        # h =  math.floor((width * current_height)/current_width)
        # return pillow.resize((width, h))
        
    # #NB the equality. On the not unlikely chance that the width 
    # # reduction is the same as the height reduction (for example, 
    # # squares), reduce by height.
    # elif (height_reduce >= width_reduce and height_reduce > 0):
        # w =  math.floor((height * current_width)/current_height)
        # return pillow.resize((w, height))
    # else:
        # return pillow

def resize_aspect(pillow, width, height):
    '''
    Resize if the image is too big, preserving aspect ratio.
    Will not resize if dimensions match or are less than the source.
    @return an image within the given dimensions. The image is usually 
    smaller in one dimension than the given space.
    '''
    s = pillow.size
    current_width = s[0]
    current_height = s[1]
    width_diff = width - current_width 
    height_diff = height - current_height
    if (height_diff > width_diff):
        # width-constrained resize
        h =  math.floor((width * current_height)/current_width)

        # clamp to something visible
        if (h <= 0):
          h = 5
        return pillow.resize((width, h))

    elif (height_diff < width_diff):
        # height-constrained resize
        w =  math.floor((height * current_width)/current_height)
        
        # clamp to something visible
        if (w <= 0):
          w = 5
        return pillow.resize((w, height))
    else:
        # source aspect matches target 
        return pillow.resize((width, height))



def crop(pillow, width, height):
    '''
    Crop if image is too big.
    Crop is anchored at centre. 
    Will not crop if both dimensions match or are less than the source.
    @return an image within the given dimensions. The image may be 
    smaller in one dimension than the given space.
    '''
    s = pillow.size
    current_width = s[0]
    current_height = s[1]
    
    width_reduce = current_width - width
    height_reduce = current_height - height

    # Only crop if the image is too big
    if ((width_reduce > 0) or (height_reduce > 0)):
        x = 0
        y = 0
        if (width_reduce > 0):
            x = width_reduce >> 1
        if (height_reduce > 0):
            y = height_reduce >> 1
        # Crop!
        pillow = pillow.crop((x, y, x + width, y + height))
    return pillow



def fill(pillow, width, height, fill_color="white"):
    '''
    Fill round an image to a box.
    Image must be smaller than the giveen box. Checking is 
    regarded as a seperate operation.
    '''
    # NB: This converts to RGB. Not an issue, as fill runs last.
    s = pillow.size
    current_width = s[0]
    current_height = s[1]

    x = (width - current_width) >> 1
    y = (height - current_height) >> 1
        
    bg = PILImage.new('RGB', (width, height), fill_color)

    # paste down.
    # I've tried a couple of ways, this mess seems to work ok
    if ((pillow.mode in ('RGBA', 'LA'))): 
        # The image has an alpha layer. But this may well be black, for
        # transparency, and on convert to RGB goes black. Solution,
        # split alpha layer and paste as mask.
        bg.paste(pillow, (x, y),  mask=pillow.getchannel('A'))
    else:
        # The image can be pasted on
        bg.paste(pillow, (x, y))
    return bg


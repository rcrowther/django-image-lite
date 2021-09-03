from image_lite.utils import url_absolute_static_aware
from wand.image import WandImage
from wand.color import Color
from wand.drawing import Drawing
import math


def photoFX(wand, pop, grayscale, warm, night, strong, no, watermark):
    if (pop):
        wand.level(0.2, 0.9, gamma=1.1)

    if (grayscale):
        # Reputedly fast and preserves transparency. Small errors 
        # will creep in, the visual effect is what matters.
        matrix = [[0.333, 0.333, 0.333],
          [0.333, 0.333, 0.333],
          [0.333, 0.333, 0.333]]
        wand.color_matrix(matrix)
        
    if (night):
        matrix = [[0.2, 0.0, 0],
           [0, 0.3, 0],
           [0, 0, 1]]
        wand.color_matrix(matrix)
        
    if (warm):
        # Yes, there are problems with HSB, but it will be ok for this.
        wand.modulate(brightness=100.0, saturation=100.0, hue=94.0)

    if (strong):
        wand.modulate(brightness=100.0, saturation=160.0, hue=100.0)

    if (no):
        insetX = wand.width >> 4
        insetY = wand.height >> 4
        insetX1 = wand.width - insetX
        insetY1 = wand.height - insetY
        with Drawing() as draw: 
            draw.stroke_color = Color('red')
            draw.stroke_width = 12
            draw.line((insetX, insetY1), (insetX1, insetY))
            draw.line((insetX, insetY), (insetX1, insetY1))        
            draw(wand)
            
    if (watermark):
        url = url_absolute_static_aware(watermark)
        scale_width = wand.width >> 1
        
        with WandImage(filename=watermark) as overlay:
            # scale the overlay to the inset.            
            overlay.resize(scale_width, round(scale_width/overlay.width * overlay.height))
            wand.composite(
                overlay, 
                left=None, 
                top=None, 
                operator='dissolve', 
                arguments='35', 
                gravity='center'
            )
    return wand


def resize_aspect(wand, width, height):
    '''
    Resize if the image is too big, preserving aspect ratio.
    Will not resize if dimensions match or are less than the source.
    @return an image within the given dimensions. The image is usually 
    smaller in one dimension than the given space.
    '''
    width_reduce = wand.width - width
    height_reduce = wand.height - height
  
    if (width_reduce > height_reduce and width_reduce > 0):
        h = math.floor((width * wand.height)/wand.width)
        wand.resize(width, h)        

    #NB the equality. On the not unlikely chance that the width 
    # reduction is the same as the height reduction (for example, 
    # squares), reduce by height.
    elif (height_reduce >= width_reduce and height_reduce > 0):
        w = math.floor((height * wand.width)/wand.height)
        wand.resize(w, height)
    return wand



def crop(wand, width, height):
    '''
    Crop if image is too big.
    Crop is anchored at centre. 
    Will not crop if both dimensions match or are less than the source.
    @return an image within the given dimensions. The image may be 
    smaller in one dimension than the given space.
    '''
    current_width = wand.width
    current_height = wand.height
    
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
        wand.crop(left=x, top=y, width=width, height=height)
    return wand


def fill(wand, width, height, fill_color="white"):
    '''
    Fill round an image to a box.
    Image must be smaller than the giveen box. Checking is 
    regarded as a seperate operation.
    '''
    current_width = wand.width
    current_height = wand.height

    with Color(fill_color) as bg:
        wand.background_color = bg
        x = (width - current_width) >> 1
        y = (height - current_height) >> 1

        # the negative is deliberate. Wand I think is anchored to *bottom* left.
        wand.extent(width=width, height=height, x=x, y=-y)

    return wand

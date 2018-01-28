import image_loader
from scipy import misc
import numpy as np
mask_fname="../static/upload/mask_diy_1515134517553.png"
im = misc.imread(mask_fname)
for i in range(im.shape[-1]):
    print np.sum(im[:,:,i])
misc.toimage(im[:,:,0]).save("c1.jpeg")
misc.toimage(im[:,:,-1]).save("c4.jpeg")

import numpy as np
from network_loader import get_conv_seq, reconstruct, Network, torchimg2pyimg, pyimg2torchimg
from image_loader import ImageLoader
import torch
import numpy as np

network = Network("exp14_50_net_G.t7")
img_loader = ImageLoader(root_dir = '/data/data/ILSVRC2010_images/val_small')
origin = img_loader.get_image_nparray_by_idx(0, -1, -1)
(width, height, nc) = origin.shape
mask = img_loader.get_random_mask(width, height)
img = img_loader.make_holes(origin, mask)
print "pyimg shape", img.shape

img = pyimg2torchimg(img)
print "torchimg shape", img.shape
fineSize = 128

img = (img * 2) - 1
img_seq, img_pos = get_conv_seq(img, fineSize, fineSize)
print "img_pos", img_pos

img_seq = torch.Tensor(img_seq)
mask_seq, _  = get_conv_seq(mask[np.newaxis, :], fineSize, fineSize)
mask_seq = torch.Tensor(mask_seq)
print "network.forward() ", mask_seq.size(), img_seq.size()

xx = img_seq.numpy()
#output_seq = network.net.forward([img_seq, mask_seq]).numpy()
#output_seq = (output_seq + 1) * 0.5

# torch image
output = np.zeros((nc, width, height))
reconstruct(output, xx, img_pos, fineSize, fineSize)

for idx, (i, j) in enumerate(img_pos):
    print np.equal(xx[idx], output[:, i:i+fineSize, j:j+fineSize]).all()

output = (output + 1) * 0.5
print "output torchimg shape", output.shape

#output = torchimg2pyimg(output)
#print "output pyimg shape", output.shape

# -*-encoding=utf-8-*-
import numpy as np
from PIL import Image
from scipy import misc
import os

IMG_ROOT = "/data/data/ILSVRC2010_images/val_small/"
IMG_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'JPG', 'JPEG'])

MAX_SIZE = 300
MIN_SIZE = 128

def read_img_names(d):
    files = os.listdir(d)
    label = d.rsplit('/', 1)[1]
    return [os.path.join(label, f) for f in files if not os.path.isdir(f) and f.rsplit('.', 1)[1] in IMG_EXTENSIONS]

def convert_fig_to_html(fig):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import StringIO
    canvas = FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    data = png_output.getvalue().encode('base64')
    return data

class ImageLoader(object):
    def __init__(self, root_dir, savepath=""):
        """
        """
        self.img_list = []
        self.label_offset = []
        offset = 0
        for item in os.listdir(root_dir):
            abs_path = os.path.join(root_dir, item)
            if os.path.isdir(abs_path):
                img_list = read_img_names(abs_path)
                self.img_list.extend(img_list)
                self.label_offset.append([offset, item])
                offset += len(img_list)
        self.size = offset
        self.root_dir = root_dir
        self.pattern = None
        self.savepath = savepath
        self.MAX_SIZE = MAX_SIZE
        self.MIN_SIZE= MIN_SIZE

    def get_image_name_by_idx(self, idx):
        if idx >= 0 and idx < self.size:
            return self.img_list[idx]
        else:
            return ""

    def get_image_nparray_by_idx(self, idx, width=-1, height=-1):
        if idx < 0 or idx > self.size:
            return None
        fpath = os.path.join(self.root_dir, self.img_list[idx])
        origin = self._load_image(fpath, width, height)
        fname = "origin_%s.jpeg" % idx
        self.save_img(origin, fname=fname)
        return origin

    def _load_image(self, fpath, width, height):
        #im = misc.imread(fpath)
        im = Image.open(fpath)
        if width == -1:
            width = max(im.size[0], self.MIN_SIZE)
        if height == -1:
            height = max(im.size[1], self.MIN_SIZE)
        max_size = max(width, height)
        if max_size > self.MAX_SIZE:
            if width > height:
                height = int(height * 1.0 / width * MAX_SIZE)
                width = self.MAX_SIZE
            else:
                width = int(width * 1.0 / height * MAX_SIZE)
                height = self.MAX_SIZE
        im = im.resize((width, height), Image.BICUBIC)
        im = np.array(im, dtype=np.float)
        im = im / 255
        return im

    def gene_pattern(self, threshold=0.25, scale=0.06, gaint_size=10000):
        w = int(gaint_size * scale)
        low_pattern = np.random.rand(w, w)
        pattern = Image.fromarray(low_pattern).resize((gaint_size, gaint_size), Image.BICUBIC) 
        pattern = np.array(pattern)
        pattern[pattern>threshold] = 1
        pattern[pattern<threshold] = 0
        self.pattern = pattern
        self.gaint_size = gaint_size

    def get_random_mask(self, width=64, height=64, lossrate=0.25):
        if self.pattern is None:
            self.gene_pattern()
        max_loop = 100
        print "get_random_mask", width, height
        i = 0
        up = width * height * (lossrate + 0.05) 
        down = width * height * (lossrate - 0.05) 
        while i < max_loop:
            x = np.random.randint(0, self.gaint_size - width)
            y = np.random.randint(0, self.gaint_size - height)
            mask = self.pattern[x:x+width,y:y+height].copy()
            area = np.sum(mask)
            if area > down and area < up:
                return mask
            i += 1
        return mask

    def make_holes(self, origin, mask):
        """
        用于python 图片[64][64][3]
        """
        img = origin.copy()
        mask_hole = np.array(1 - mask, dtype=np.bool_)
        img[:,:,0][mask_hole] = 117.0 / 255
        img[:,:,1][mask_hole] = 104.0 / 255
        img[:,:,2][mask_hole] = 123.0 / 255
        return img

    def _load_img(self, im, nc):
        im = np.array(im, dtype=np.float32) / 255
        if len(im.shape) == 3 and im.shape[-1] != nc:
            if im.shape[2] == 4 and nc == 3:
                return im[:,:,0:3]
            elif (im.shape[2] == 4 or im.shape[2] == 3) and nc == 1:
            # 红色遮罩，所以取第1个通道,png图片取第4个遮罩也没问题
                return im[:,:,0]
        return im

    def load_img(self, fname, nc=3, savepath=None):
        """
        读文件
        """
        savepath = savepath or self.savepath
        im = misc.imread(os.path.join(savepath, fname))
        return self._load_img(im, nc)

    def read_img(self, f, nc):
        """
        读对象
        """
        im = misc.imread(f)
        return self._load_img(im, nc)

    def save_img(self, img, fname, savepath=None):
        savepath = savepath or self.savepath
        misc.toimage(img, cmin=0, cmax=1).save(os.path.join(self.savepath, fname))
        print "save to path: %s" % os.path.join(self.savepath, fname)





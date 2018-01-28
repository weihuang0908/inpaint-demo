# -*-encoding=utf-8-*-
import torch
import os
import json
from torch.utils.serialization import load_lua
from torch.legacy.nn.SpatialConvolution import SpatialConvolution
from torch.legacy.nn.SpatialFullConvolution import SpatialFullConvolution
from torch.legacy.nn.SpatialBatchNormalization import SpatialBatchNormalization
import numpy as np
import base64
from scipy import misc

NET_ROOT = "/home/huangwei/context-encoder/checkpoints/"
exp26 = "exp26_50_net_G.t7"
exp26_Q = "exp26_50_net_Q.t7"

def find_modules(net, cls):
    return [item for item in net.listModules() if type(item) == cls]

def init_finput(m):
    """
    从lua读入反卷积层的时候，finput, fgradInput不存在，这在后续的forward中会报错
    为啥卷积层没问题，原因不详
    """
    m.finput = None
    m.fgradInput = None

def get_conv_seq(x, oW, oH):
    """
    for torch image
    """
    (nc, iH, iW) = x.shape
    assert(nc <= 3)
    fine_list = []
    pos_list = []
    def getRange(iw, ow, step):
        """
        若边界不能整除，最右列和最下行可能与邻居重叠
        """
        seq = [i for i in range(0, iw-ow+1, step)]
        if seq[-1] + ow < iw:
            seq.append(iw-ow)
        return seq
    for i in getRange(iH, oH, oH-1):
        for j in getRange(iW, oW, oW-1):
            fine = x[:, i:i+oH, j:j+oW]
            fine_list.append(fine)
            pos_list.append((i, j))
    return np.stack(fine_list), pos_list

def reconstruct(output, data, pos, w, h):
    """
    for torch image
    """
    for idx, (i, j) in enumerate(pos):
        output[:, i:i+h, j:j+w] = data[idx]

def tensor(x, add_axis=True):
    if not torch.is_tensor(x):
        x = torch.Tensor(x)
    if add_axis:
        x = torch.unsqueeze(x, 0)
    return x

def torchimg2pyimg(x):
    # 把[3,64,64]映射成[64,64,3]
    (nc, w, h) = x.shape
    data = np.zeros([w, h, nc], dtype=np.float32)
    for c in range(nc):
        data[:,:,c] = x[c,:,:]
    return data

def pyimg2torchimg(x):
    # 把[64,64,3]映射成[3,64,64]
    (w, h, nc) = x.shape
    data = np.zeros([nc, w, h], dtype=np.float32)
    for c in range(nc):
        data[c,:,:] = x[:,:,c]
    return data

def print_output_sum(net):
    for i, l in enumerate(net.modules):
        if hasattr(l, "modules"):
            print_output_sum(l)
        else:
            print "sum of %d layer\t %f" % (i, torch.sum(l.output))
        
class Network(object):
    def __init__(self, fname=exp26):
        self.path = os.path.join(NET_ROOT, fname)
        self.net = load_lua(self.path)
        self.net.evaluate()
        self.conv_list = find_modules(self.net, SpatialConvolution)
        self.full_conv_list = find_modules(self.net, SpatialFullConvolution)
        self.batch_norm_list = find_modules(self.net, SpatialBatchNormalization)
        self.with_mask = False
        self.fineSize = 128
        if self.conv_list[0].nInputPlane == 4:
            self.with_mask = True
        map(init_finput, self.full_conv_list)

    def hello(self):
        return str(self.net)

    def find_conv(self):
        conv_list = find_modules(self.net, SpatialConvolution)
        return conv_list

    def get_conv_weight(self, idx):
        """
        返回给定某层的权重矩阵
        """
        try:
            idx = int(idx)
        except Exception, e:
            return json.dumps({"success": -1, "err_msg": "%s should be int" % idx})
        length = len(self.conv_list)
        if idx < length and idx >= 0:
            weight =self.conv_list[idx].weight 
            data = weight.tolist() 
            shape = list(weight.size())
            return json.dumps({"success": 0, "data": data, "shape": shape})
        return json.dumps({"success": -1, "err_msg": "%d out of the bound" % idx})

    def forward_small(self, img, mask):
        """
        这里认为img和mask与神经网络的输入尺寸匹配
        mask 2维
        img 3维
        """
        img = (img * 2) - 1
        img = tensor(pyimg2torchimg(img), add_axis=True) 
        if self.with_mask == 1:
            mask = tensor(mask[np.newaxis,:], add_axis=True) 
            output = self.net.forward([img, mask]).squeeze(0).numpy()
        else:
            output = self.net.forward(img).squeeze(0).numpy()
        output = (output + 1) * 0.5
        return torchimg2pyimg(output)

    def forward(self, img, mask):
        """
        任意尺寸
        """
        img = pyimg2torchimg(img)
        img = (img * 2) - 1
        img_seq, img_pos = get_conv_seq(img, self.fineSize, self.fineSize)
        img_seq = torch.Tensor(img_seq)
        if self.with_mask == 1:
            mask_seq, _  = get_conv_seq(mask[np.newaxis, :], self.fineSize, self.fineSize)
            mask_seq = torch.Tensor(mask_seq)
            print "network.forward() ", mask_seq.size(), img_seq.size()
            output_seq = self.net.forward([img_seq, mask_seq]).numpy()
        else:
            output_seq = self.net.forward(img_seq).numpy()
        output = np.copy(img)
        reconstruct(output, output_seq, img_pos, self.fineSize, self.fineSize)
        output = (output + 1) * 0.5
        return torchimg2pyimg(output)

class NetworkQ(Network):
    def __init__(self, fname=exp26_Q):
        self.path = os.path.join(NET_ROOT, fname)
        self.net = load_lua(self.path)
        self.net.evaluate()
        self.conv_list = find_modules(self.net, SpatialConvolution)
        self.full_conv_list = find_modules(self.net, SpatialFullConvolution)
        self.batch_norm_list = find_modules(self.net, SpatialBatchNormalization)
        map(init_finput, self.full_conv_list)
        self.fineSize = 128

    def forward(self, img):
        """
        判别器的forward
        """
        img = pyimg2torchimg(img)
        img = (img * 2) - 1
        img_seq, img_pos = get_conv_seq(img, self.fineSize, self.fineSize)
        img_seq = torch.Tensor(img_seq)
        output_seq = self.net.forward(img_seq).numpy()
        output = np.copy(img)
        reconstruct(output, output_seq, img_pos, self.fineSize, self.fineSize)
        return torchimg2pyimg(output)

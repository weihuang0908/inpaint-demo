# -*-encoding=utf-8-*-
import os
from flask import Flask, request, Response, redirect, url_for
from flask import send_from_directory
from models.network_loader import Network, NetworkQ
from models.image_loader import ImageLoader
from werkzeug import secure_filename
import numpy as np
import json

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'JPG', 'JPEG'])

app = Flask(__name__)
app.config['UPLOAD_DIR'] = "static/upload"
app.config['OUTPUT_DIR'] = "static/output"
app.config['VAL_IMG_DIR'] = "/data/data/ILSVRC2010_images/val_small"

exp26 = "exp26_50_net_G.t7"
exp14 = "exp14_50_net_G.t7"
exp14_Q = "exp14_50_net_Q.t7"
finesize = 128
MAX_SIZE = 400
MIN_SIZE = 128
network = Network(fname=exp14)
network_Q = NetworkQ(fname=exp14_Q)
network.fineSize = finesize
img_loader = ImageLoader(root_dir = app.config['VAL_IMG_DIR'], savepath=app.config["OUTPUT_DIR"])
img_loader.MAX_SIZE = MAX_SIZE
img_loader.MIN_SIZE = MIN_SIZE

@app.route('/')
def hello_world():
    return app.send_static_file('index.html')

@app.route('/api/get_conv_weight/<idx>')
def get_conv_weight_by_idx(idx):
    return network.get_conv_weight(idx)

def check_file(f):
    def allowed_file(filename):
        return '.' in filename and \
                filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    if f and allowed_file(f.filename):
        filename = secure_filename(f.filename)
        return filename
    return None


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        filename = check_file(f)
        if filename:
            f.save(os.path.join(app.config['UPLOAD_DIR'], filename))
            return json.dumps({"success": 0, "url":"/api/view/uploaded/%s" % filename});
        else:
            return json.dumps({"success": -1, "error_msg": "file type not allowed"});
    return json.dumps({"success": -1, "error_msg": "should post!"});

@app.route('/api/view/uploaded/<filename>')
def view_uploaded_img(filename):
    return send_from_directory(app.config['UPLOAD_DIR'], filename)

@app.route('/api/view/predefined/<idx>')
def view_predefined_img(idx):
    try:
        idx = int(idx)
    except Excpteion, e:
        return "error: idx should be int"
    filename = img_loader.get_image_name_by_idx(idx)
    return send_from_directory(app.config['VAL_IMG_DIR'], filename)

def _gene_mask(mask_fname, width=finesize, height=finesize):
    assert(width > 0 and height > 0)
    print "_gene_mask", width, height
    mask = img_loader.get_random_mask(width=width, height=height)
    img_loader.save_img(mask, fname=mask_fname)
    return mask

@app.route('/api/view/mask')
def view_mask():
    sid = request.args.get('sid') or ""
    mask_fname = "mask_%s.png" % sid
    if not os.path.isfile(os.path.join(app.config['OUTPUT_DIR'], mask_fname)):
        _gene_mask(mask_fname)
    return send_from_directory(app.config['OUTPUT_DIR'], mask_fname)

def get_in_out_mask_names(flag, sid):
    base = ["input_%s_%s.jpeg", "output_%s_%s.jpeg", "mask_%s_%s.png"]
    return map(lambda x: x % (flag, sid), base)

def _inpaint(isSmall, origin, mask, input_fname, output_fname):
    """
    mask 0 为洞， 1 为ctx
    """
    assert(mask.shape[0] == origin.shape[0])
    assert(mask.shape[1] == origin.shape[1])
    # 打洞
    img = img_loader.make_holes(origin, mask)
    # 补洞
    if isSmall:
        output = network.forward_small(img, mask)
    else:
        output = network.forward(img, mask)
    outputQ = network_Q.forward(output)
    # 存盘
    img_loader.save_img(img, fname=input_fname)
    img_loader.save_img(output, fname=output_fname)
    img_loader.save_img(outputQ, fname="Q_" + output_fname)

def inpaint(isSmall, sid, job, refresh_mask, width, height):
    # 填上文件名
    flag = "small" if isSmall else "origin"
    input_fname, output_fname, mask_fname = get_in_out_mask_names(flag, sid)
    # job决定哪张图片
    origin = img_loader.get_image_nparray_by_idx(job, width, height)
    if refresh_mask:
        if width == -1:
            width = origin.shape[0]
        if height == -1:
            height = origin.shape[1]
        mask = _gene_mask(mask_fname, width, height)
        img_loader.save_img(mask, fname=mask_fname)
    else:
        mask = img_loader.load_img(mask_fname)
    _inpaint(isSmall, origin, mask, input_fname, output_fname)
    origin_fname = "origin_%s.jpeg" % job
    return json.dumps({"success": 0, 
            "input_url": "/api/view/%s" % input_fname,
            "g_output_url": "/api/view/%s" % output_fname,
            "q_output_url": "/api/view/Q_%s" % output_fname,
            "mask_url": "/api/view/%s" % mask_fname,
            "origin_url": "/api/view/%s" % origin_fname,
            })

@app.route('/api/view/<fname>')
def view_img(fname):
    return send_from_directory(app.config['OUTPUT_DIR'], fname)


@app.route('/api/inpaint_small/<job>')
def inpaint_small(job):
    """
    128*128， 一次喂给神经网络
    """
    try:
        job = int(job)
        refresh_mask = int(request.args.get('refresh_mask', 1))
        sid = request.args.get('sid') or ""
    except Exception, e:
        return json.dumps({"success": -1, "err_msg": str(e)})
    return inpaint(True, sid, job, refresh_mask, finesize, finesize)

@app.route('/api/inpaint/<job>')
def inpaint_origin(job):
    """
    任意尺寸，拆成小块再合成
    """
    try:
        job = int(job)
        width = int(request.args.get('width', -1)) 
        height = int(request.args.get('height', -1))# if request.args.get('height') else -1
        refresh_mask = int(request.args.get('refresh_mask', 1))
        sid = request.args.get('sid') or ""
    except Exception, e:
        return json.dumps({"success": -1, "err_msg": str(e)})
    return inpaint(False, sid, job, refresh_mask, width, height)

@app.route('/api/inpaint_diy', methods=['POST'])
def inpaint_diy():
    if request.method == 'POST':
        sid = request.form.get("sid", "")
        # 检查上传的origin和mask图片是否合法
        origin_f = request.files['origin_f']
        origin_fname = check_file(origin_f)
        mask_f = request.files['mask_f']
        mask_fname = check_file(mask_f)
        input_fname, output_fname, mask_fname = get_in_out_mask_names("diy", sid)
        if origin_fname and mask_fname:
            origin = img_loader.read_img(origin_f, 3)
            mask = img_loader.read_img(mask_f, 1)
            _inpaint(False, origin, 1 - mask, input_fname, output_fname)
            return json.dumps({"success": 0, 
                    "input_url": "/api/view/%s" % input_fname,
                    "g_output_url": "/api/view/%s" % output_fname,
                    "q_output_url": "/api/view/Q_%s" % output_fname,
                    "mask_url": "/api/view/%s" % mask_fname,
                    })
        else:
            return json.dumps({"success": -1, "error_msg": "origin or mask file not found"});
    return json.dumps({"success": -1, "error_msg": "should post!"});

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

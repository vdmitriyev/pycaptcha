# -*- coding: utf-8 -*-

import os
import uuid
import codecs
import random
import  argparse
import string
import datetime
import logging.config
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request, make_response, jsonify, send_from_directory

SERVER_IP = '127.0.0.1'
SERVER_PORT = '5000'
LOGS_FOLDER = '.logs'
JOBS_FOLDER = '.captchas'

def init_work_env():
    ''' Initialize working environment'''

    # create logs folder
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)

    # create jobs folder
    if not os.path.exists(JOBS_FOLDER):
        os.makedirs(JOBS_FOLDER)

init_work_env()

# proper logging in flask via confi file
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

# start/create flask app
app = Flask("PyCaptcha Simplified")
CORS(app)

@app.route('/')
def index():

    html_content = '''<html>
                    <head>
                        <style>
                            li{{margin:5px; padding-top:5px}};
                        </style>
                    </head>
                    <body>
                    <h2>Welcome to the "PyCaptcha Simplified" backend!</h2>
                    It's very simple web API server for the captcha generation.</br></br>
                    Please, use following APIs:<br>
                    <ul>
                        <li>
                            <a href="http://{address}:{port}/getCaptcha">http://{address}:{port}/getCaptcha</a>
                            <ul>
                                <li><b>POST / GET</b></li>
                            </ul>
                        </li>
                        <li>
                            <a href="http://{address}:{port}/checkCaptcha">http://{address}:{port}/checkCaptcha</a>
                            <ul>
                                <li><b>POST</b></li>
                                <li>SAMPLE PAYLOAD: <a href={payloadCheckCaptcha}>{payloadCheckCaptcha}</a></pre></li>
                            </ul>
                        </li>
                    </ul>
                    </body>
                    </html>
                    '''.format(address=SERVER_IP,
                               port=SERVER_PORT,
                               payloadCheckCaptcha='tests/payload-check-captcha.json')

    return html_content

@app.route('/captchas/<path:path>')
def send_captchas(path):
    logger.info('Follwing URI was requested (captchas folder): {0}'.format(path))
    return send_from_directory('.captchas', path)

@app.route('/getCaptcha', methods=['GET', 'POST'])
def getCaptcha():
    '''Receive a request for a new captcha, generates it and returns id.'''

    #if request.method == 'POST'

    captcha_job_id = '{0}-{1}'.format(datetime.datetime.today().strftime('%Y%m%d-%H%M'),str(uuid.uuid4())[:8])
    response = {'captchaId' : captcha_job_id}

    response_body = dict()

    new_captcha_path = os.path.join(JOBS_FOLDER, captcha_job_id)

    if not os.path.exists(new_captcha_path):

        os.makedirs(new_captcha_path)

        captcha_path = os.path.join(new_captcha_path, captcha_job_id) + '.png'
        captcha_uri = 'captchas/{0}/{0}.png'.format(captcha_job_id)
        captcha_path_answer = os.path.join(new_captcha_path, captcha_job_id) + '.ans'

        captcha_text = generate_captcha(captcha_path, add_noise=False)
        #captcha_text = generate_captcha(captcha_path, add_noise=True)

        # save captcha value
        with open(captcha_path_answer, 'w') as _f_ans:
            _f_ans.write(captcha_text)

        response['captchaURI'] =  'http://{server}:{port}/{uri}'.format(server=SERVER_IP,
                                                                        port=SERVER_PORT,
                                                                        uri=captcha_uri)
        response_body['response'] = response
        response_code = 200
    else:
        response_body['response'] = 'Something went wrong!'
        response_code = 500

    return make_response(jsonify(response_body), response_code)

@app.route('/checkCaptcha', methods=['GET', 'POST'])
def checkCaptcha():
    '''Recieve a job ID and checks captcha, if available.'''

    if request.method == 'POST':
        requst_json = request.get_json(force=True)
        captcha_id = requst_json.get('captchaId', None)
        captcha_value = requst_json.get('captchaValue', None)
    else:
        captcha_id =  request.args.get('captchaId', None)
        captcha_value = request.args.get('captchaValue', None)

    response_body = dict()
    response_code = 200

    captcha_path = os.path.join(JOBS_FOLDER, captcha_id)
    captcha_path_image = os.path.join(captcha_path, captcha_id) + '.png'
    captcha_path_answer = os.path.join(captcha_path, captcha_id) + '.ans'

    if captcha_id is None or captcha_value is None:
        response_body['response'] = {'status' : 'wrong-parameters'}
        response_code = 404
    elif not os.path.exists(captcha_path):
        response_body['response'] = {'status' : 'requestId-unknown'}
        response_code = 404
    elif not os.path.exists(captcha_path_image) or not os.path.exists(captcha_path_answer):
        response_body['response'] = {'status' : 'no-captcha-found'}
        response_code = 404
    elif os.path.exists(captcha_path_image) and os.path.exists(captcha_path_answer):

        with open(captcha_path_answer, 'r') as _file:
            f_content = _file.read().strip()

        if f_content == captcha_value:
            response_body['response'] = {'status' : 'ok', 'captchaVerdict' : 'correct'}
            response_code = 200
        else:
            response_body['response'] = {'status' : 'ok', 'captchaVerdict' : 'wrong'}
            response_code = 200
    else:
          response_body['response'] = {'status' : 'unhandled-situation'}
          response_code = 500

    return make_response(jsonify(response_body),response_code)

#
# Utilities / Helpers
#

def generate_captcha(image_path, add_noise = False):
    ''' Generate a captcha and return the solution of the captcha'''

    _captcha_txt = get_random_text(length=4)

    _font = ImageFont.truetype("arial.ttf", 40)
    _image = Image.new('RGB', (200, 200), color = (255, 255, 255))
    _drawing = ImageDraw.Draw(_image)

    if add_noise:
        add_noise_arcs(_drawing, _image)
        add_noise_dots(_drawing, _image)

    _drawing.text((45,75), _captcha_txt, font=_font, fill=(0, 0, 0))
    _image.save(image_path)
    return _captcha_txt

def add_noise_arcs(draw, image):
    size = image.size
    rand_v1 = random.randint(0, size[0])
    rand_v2 = random.randint(size[0]/2, size[0])
    draw.arc([-rand_v1, -rand_v1, size[0], rand_v1], 0, 295, fill=(0, 0, 0))
    draw.line([-rand_v1, rand_v1, size[0] + rand_v1, size[1] - rand_v1], fill=(0, 0, 0))
    draw.line([-rand_v2, 0, size[0] + rand_v2, size[1]], fill=(0, 0, 0))

def add_noise_dots(draw, image):
    size = image.size
    rand_b = random.randint(50, 250)
    for p in range(int(size[0] * size[1] * 0.2)):
        draw.point((random.randint(0, size[0]), random.randint(0, size[1])), fill=(0, 0, rand_b))

def get_random_text(length=8):
    #chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    chars = string.digits
    return ''.join(random.choice(chars) for x in range(length))

def genrate_training_data():
    '''Generate training data for the further usage'''
    print ('[i] Generating a train dataset')

    TRAIN_FOLDER = 'train'

    # create jobs folder
    if not os.path.exists(TRAIN_FOLDER):
        os.makedirs(TRAIN_FOLDER)

    #symbols = string.digits + string.ascii_uppercase + string.ascii_lowercase
    symbols = string.digits

    #'consola.ttf'
    #font_styles = ['arial.ttf', 'tahoma.ttf', 'times.ttf', 'comic.ttf', 'calibri.ttf']
    font_styles = ['arial.ttf']

    _fonts = [ImageFont.truetype(x, 40) for x in font_styles]
    for letter in symbols:

        image_folder = os.path.join(TRAIN_FOLDER, letter)

        # create jobs folder
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        SAMPLES = 500
        # save test data as images
        for index, font in enumerate(_fonts):
            for _x in range(SAMPLES):
                _image_path = os.path.join(image_folder, '{0}-{1}-image.png'.format(index, _x))
                _image = Image.new('RGB', (30, 30), color = (255, 255, 255))
                _drawing = ImageDraw.Draw(_image)
                font_width, font_height = font.getsize(letter)
                font_y_offset = font.getoffset(letter)[1] # <<<< MAGIC!
                #_drawing.text((0,0), letter, font=font, fill=(255, 255, 255))
                _drawing.text((4, 0 - font_y_offset+1), letter, font=font, fill=(0, 0, 0))
                _image.save(_image_path)

if __name__ == '__main__':
    # construct the argument parse and parse the arguments

    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--mode", required=True, help="path to input image")
    ap.set_defaults(mode='SERVER')
    args = vars(ap.parse_args())

    if args['mode'].upper() == 'GENERATE':
        genrate_training_data()

    if args['mode'].upper()     == 'SERVER':
        app.run(debug=True)


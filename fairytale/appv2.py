'''
file: appv2.py
author: Guyoung Kwon
date: 2022.09.19
memo:
    전달받는 데이터: 이미지, 텍스트
    처리 프로세스: 
        1. 텍스트 데이터를 colab으로 전송
        2. 생성된 background 이미지 받아오기
        3. 입력받은 이미지의 데이터 mask데이터 생성
        4. background이미지와 mask이미지 합성
        5. 합성된 이미지 서버로 response
'''
from flask import Flask, request, Response
import cv2
import requests
import json
import base64
import jsonpickle
import numpy as np
import maskGen
from blenImage import blendImage


app = Flask(__name__)
app.debug=True

addr_spring = 'http://192.168.0.116:5003' + '/receive/image'
addr_colab = 'http://8435-34-132-200-219.ngrok.io' + '/gettext'

def decodeImage(data, name):
    # 이미지를 디코딩하고 저장
    img = base64.b64decode(data)
    nparr = np.fromstring(img, dtype=np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (512, 512))

    cv2.imwrite('static/data/' + name + '.png', img)
    print('saved ' + name + ' image')

def imageBlend():
    source_file = 'static/data/origin.png'
    mask_file = 'static/data/mask_image.png'
    target_file = 'static/data/back_ground.png'
    blendImage(source_file, mask_file, target_file)
    # cv2.imread('static/images/data_second_pass.png')
    final_data = cv2.imread('static/images/data_second_pass.png')
    sendMessage(final_data, 'image', addr_spring)

def getMask(data):
    maskGen.create_mask(data)
    cv2.imread('static/data/mask_image.png')
    imageBlend()

@app.route('/getmessage', methods=['POST'])
def getMessage():
    if request.method == 'POST':
        # For json communicatoin
        if request.is_json:
            r = request.get_json()

        # send text data to colab flask
        sendMessage(r['text'], 'text', addr_colab)

        # decode image data and make mask image
        data = cv2.imread('static/data/iu_test.jpg')
        _, data = cv2.imencode('.png', data)
        data = base64.encodebytes(data).decode('utf-8')
        # decodeImage(r['image'][0], 'origin')
        decodeImage(data, 'origin')

        # load origin image and make mask image
        img = cv2.imread('static/data/origin.png')
        getMask(img)
    
    response = {"msg":'Successfully received data'}
    
    # encode response
    response = jsonpickle.encode(response)
    return Response(response=response, status = 200, mimetype='application/json')



def sendMessage(data, type, addr):
    # prepare headers for http request
    content_type = 'application/json'
    headers = {'content-type': content_type, 'charset':'utf-8'}
    
    if type == 'image':
        print('send image')
        # encoding with base64
        _, img = cv2.imencode('.png', data)
        img = base64.encodebytes(img).decode('utf-8')
        data = {"title": type, "image":img}
        data = json.dumps(data)
        # send http request with image and receive response
        response = requests.post(addr, data=data, headers=headers)

    elif type == 'text':
        print('send text')
        data = {"data":data}
        data = json.dumps(data)
        # send http request with image and receive response
        response = requests.post(addr, data=data, headers=headers)
        # decode image
        decodeImage(response.text, 'back_ground')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 5001)
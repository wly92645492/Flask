# 注册和登录
from  . import passport_blue
from flask import request

@passport_blue.route('/image_code',methods=['GET'])
def image_code():
    '''提取图片验证码'''
    print(request.url)
    pass


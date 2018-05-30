# 注册和登录
from  . import passport_blue
from flask import request,abort,current_app,make_response,jsonify,session,json

from info.utils.captcha.captcha import captcha
from info import redis_store,constants,response_code,db
import  re, random, datetime
from info.libs.yuntongxun.sms import CCP
from info.models import User


@passport_blue.route('/logout',methods=['GET'])
def logout():
    '''退出登录'''
    #清理session
    try:
        session.pop('user_id',None)
        session.pop('mobile',None)
        session.pop('nick_name',None)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR,errmsg='退出登录失败')

    return jsonify(errno=response_code.RET.OK,errmsg='退出登录成功')


@passport_blue.route('/login',methods=['POST'])
def login():
    '''登录
    1.获取参数（手机号，密码明文）
    2.校验参数 （判断参数是否缺少和手机号是否合法）
    3.使用手机号查询用户信息
    4.校验用户和密码是否正确
    5.将状态保持信息写入到session，完成登录
    6.记录最后一次登录之间
    7.响应登录结果
    '''
    #1.获取参数（手机号，密码明文）
    json_dict = request.json
    mobile = json_dict.get('mobile')
    password = json_dict.get('password')

    #2.校验参数
    if not all([mobile,password]):
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='缺少参数')
    if not re.match(r'^1[345678][0-9]{9}$',mobile):
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='手机号格式错误')
    # 3.还使用手机号查询用户信息
    try:
        user = User.query.filter(User.mobile==mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询用户数据失败')
    if not user:
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='用户名或密码错误')

    # 4.校验用户密码是否正确
    if not user.check_password(password):
        return jsonify(errno=response_code.RET.PWDERR, errmsg='用户名或密码错误')

    # 5.将状态保持信息写入到session,完成登录
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name

    # 6.记录最后一次登录的时间
    user.last_login = datetime.datetime.now()
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=response_code.RET.DBERR, errmsg='记录最后一次登录的时间失败')

    # 7.响应登录结果
    return jsonify(errno=response_code.RET.OK, errmsg='登录成功')



@passport_blue.route('/register',methods=['POST'])
def register():
    '''
    注册
    1.接收参数（手机号，短信验证码。密码明文）
    2.校验参数（判断是否缺少和手机号是否合法）
    3.查询服务器的短信验证码
    4.跟客户端传入的短信验证码对比
    5.如果对比成功， 就创建user模型对象，并对属性赋值
    6.将模型数据同步到数据库
    7.保存session，实现状态保持，注册及登录
    8.响应注册结果
    '''

    # 1.接收参数（手机号，验证码，密码明文）
    # request.json:封装类json.loads(request.data)
    json_dict = request.json
    mobile = json_dict.get('mobile')
    smscode_client = json_dict.get('smscode')
    password = json_dict.get('password')
    # print(json_dict)

    # 2.校验参数（判断是否缺少和手机号是否合法
    if not all([mobile,smscode_client,password]):
        return jsonify(erron=response_code.RET.PARAMERR,errmsg='缺少参数')
    if not re.match(r'^1[345678][0-9]{9}$',mobile):
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='手机号格式错误')

    # 3.查询服务器的短信验证码
    try:
        smscode_server = redis_store.get('SMS:' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='查询短信验证码失败')
    if not smscode_server:
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='短信验证码不存在')

    # 4.跟客户端传入的短信验证码对比
    if smscode_client != smscode_server:
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='输入验证码有误')

    # 5.如果对比成功， 就创建User模型对象，并对属性赋值
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    # TODO 密码需要加密后再存储

    user.password = password  # setter方法
    # 记录最后一次登录的时间
    user.last_login = datetime.datetime.now()

    # 6.将模型数据同步到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=response_code.RET.DBERR, errmsg='保存注册数据失败')


    # 7.保存session，实现状态保持，注册及登录
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name

    # 8.响应注册结果
    return jsonify(errno=response_code.RET.OK,errmsg='注册成功')





@passport_blue.route('/sms_code',methods=['POST'])
def sms_code():
    '''发送短信
    1.接收参数（手机号，图片验证码，uuid）
    2.校验参数是否齐全
    3.查询服务器存储的图片验证码
    4.跟客户传入的图片验证码对比
    5.如果对比成功，生成短信验证码。并发送短信
    6.存储短信验证码到redis，方便注册时比较
    7.响应短信验证码发送的结果
    '''
    # 1.接收参数
    json_str = request.data
    json_dict = json.loads(json_str)
    mobile = json_dict.get('mobile')
    image_code_client = json_dict.get('image_code')
    image_code_id = json_dict.get('image_code_id')

    # 2.校验参数是否齐全，手机号是否合法
    if not all ([mobile,image_code_client,image_code_id]):
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='缺少参数')
    if not re.match(r'^1[345678][0-9]{9}$',mobile):
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='手机号格式错误')

    # 3.查询服务器存储的图片验证码
    try:
        image_code_server = redis_store.get('ImageCode:'+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR,errmsg='查询验证码失败')
    if not image_code_server:
        return jsonify(errno=response_code.RET.NODATA,errmsg='图片验证不存在')

    # 4.跟客户端传入的图片验证码对比
    if image_code_server.lower() != image_code_client.lower():
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='输入验证码有误')

    # 5.如果对比成功，生成短信验证码，并发送短信
    # '%06d':如果不够6位，补0，比如28--000028
    sms_code = '%06d' % random.randint(0,999999)
    # result = CCP().send_template_sms(mobile,[sms_code,5],1)
    # if result !=0:
    #     return jsonify(errno=response_code.RET.THIRDERR,errmsg='发送短信验证码失败')
    print(sms_code)

    # 6.存储短信验证码到redis，方便注册时比较
    try:
        redis_store.set('SMS:'+mobile,sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR,errmsg='保存短信验证码失败')

    # 7.响应短信验证码发送的结果
    return jsonify(errno=response_code.RET.OK,errmsg='发送短信验证码成功')


@passport_blue.route('/image_code',methods=['GET'])
def image_code():
    '''提取图片验证码
    1.接收参数（uuid)
    2.校验参数（判断uuid是否为空）
    3.生成图片验证码
    4.保存图片验证码到redis
    5.修改image的ContentType = 'image/jpg'
    6.响应图片验证码

    '''
    #1.接收参数（uuid）
    imageCodeId = request.args.get('imageCodeId')
    #2.校验参数（判断uuid是否为空）
    if not imageCodeId:
        abort(403)

    #3.生成图片验证码
    name, text, image = captcha.generate_captcha()

    #4.保存图片验证码到redis
    try:
        redis_store.set('ImageCode:'+imageCodeId,text,constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)

    #5.修改image的ContentType = 'image/jpg'
    response = make_response(image)
    response.headers['Content-Type'] = 'image/jpg'

    #6.响应图片验证码
    return response


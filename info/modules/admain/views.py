#后台管理
from flask import current_app
from flask import redirect
from flask import session
from flask import url_for

from info.models import User
from . import admin_blue
from flask import request,render_template


@admin_blue.route('/login',methods=['GET','POST'])
def admin_login():
    '''管理员登录'''
    #GET:提供登录界面
    if request.method == 'GET':
        return render_template('admin/login.html')

    #POST：实现登录的
    if request.method == 'POST':
        #1.获取参数
        username = request.form.get('username')
        password = request.form.get('password')

        #2.校验参数
        if not all ([username,password]):
            return render_template('admin/login.html',errmsg='缺少参数')

        #3.查询当前要登录的用户是否存在
        try:
            user = User.query.filter(User.nick_name==username).first()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/login.html',errmsg='缺少参数')
        if not user:
            return render_template('admin/login.html',errmsg='用户名或密码错误')

        #4.对比当前要登录的用户是否存在
        if not user.check_password(password):
            return render_template('admin/login.html',errmsg='用户名或密码错误')

        #5.将状态保持信息写入session
        session['user_id'] = user.id
        session['nick_name'] = user.nick_name
        session['mobile'] = user.mobile
        session['is_admin'] = user.is_admin

        #6.响应登录结果
        return redirect(url_for('admin.admin_index'))


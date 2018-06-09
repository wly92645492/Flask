from flask import Blueprint,session,redirect,url_for
from flask import request

admin_blue = Blueprint('admin', __name__,url_prefix='/admin')

from . import views


@admin_blue.before_request
def check_admin():
    '''验证用户身份是否是admin'''
    is_admin = session.get('is_admin',False)

    #1.判断是否是管理员：只有管理员才能进入后台管理
    #2.当无论是那种用户访问后台管理的登录界面，都是可以正常进入的
    #2.1如果是前台用户，可以登录，但是登录后的操作会被卡住
    # 2.2如果是后台用户可以登录，因为就是他的逻辑
    #2.3小猪佩奇输入 http://127.0.0.1:5000/admin/login
    #3.如果管理员进入后台，又误入前台，退出时会留下私生子（session is_admin = True

    if not is_admin and not request.url.endswith('/admin/login') and not request.url.endswith('/admin/user_count'):
        return redirect(url_for('index.index'))
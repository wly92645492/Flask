from flask import Blueprint,session,redirect,url_for

admin_blue = Blueprint('admin', __name__,url_prefix='/admin')

from . import views


@admin_blue.before_request()
def check_admin():
    '''验证用户身份是否是admin'''
    is_admin = session.get('is_admin',False)

    #判断是否是管理员
    if not is_admin:
        return redirect(url_for('index.index'))
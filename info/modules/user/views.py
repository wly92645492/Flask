#个人中心
from flask import g

from info.utils.comment import user_login_data
from . import user_blue
from flask import render_template

@user_blue.route('/info')
@user_login_data
def user_info():
    '''个人中心入口'''
    user = g.user
    context = {
        'user':user
    }
    return render_template('/news/user.html',context=context)
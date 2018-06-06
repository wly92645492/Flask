#个人中心
from flask import current_app
from flask import g, jsonify
from flask import request
from flask import session
from flask import url_for
from info import response_code, db,constants
from info.utils.comment import user_login_data
from flask import render_template,redirect
from info.utils.file_storage import upload_file
from . import user_blue
from info.models import check_password_hash,Category, News


@user_blue.route('/news_list')
@user_login_data
def user_news_list():
    '''我发布的新闻列表'''
    #1.获取登录用户信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 2.接受参数
    page = request.args.get('p', '1')

    # 3.校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = '1'

    # 4.分页查询
    news_list = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)

        # 5.构造渲染数据
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    context = {
        'news_list': news_dict_list,
        'current_page': current_page,
        'total_page': total_page
    }

    # 6.渲染界面
    return render_template('news/user_news_list.html', context=context)


@user_blue.route('/news_release',methods=['GET','POST'])
@user_login_data
def news_release():
    '''用户新闻发布'''
    #1判断用户登录信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    #2.请求方法为GET方法：渲染新闻分类
    if request.method == 'GET':
        #2.1渲染新闻分类
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)

        #删除最新分类
        categories.pop(0)
        context = {
            'categories':categories
        }
        return render_template('news/user_news_release.html',context=context)

    #3.请求方法为POST
    if request.method == 'POST':
        #3.1接收参数
        title = request.form.get('title')
        source = '个人发布'
        digest = request.form.get('digest')
        content = request.form.get('content')
        indext_image = request.files.get('index_image')
        category_id = request.form.get('category_id')

        #3.2校验参数
        if not all([title,source,digest,content,indext_image,category_id]):
            return jsonify(errno = response_code.RET.PARAMERR,errmsg='缺少参数')


        #3.3读取用户上传的新闻图片
        try:
            indext_image_data = indext_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno = response_code.RET.PARAMERR,errmsg='读取新闻数据失败')

        #3.4将用户上传的图片转存到七牛云
        try:
            key = upload_file(indext_image_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.THIRDERR,errmsg='上传新闻图片失败')

        #3.5创建News新闻模型对象，并赋值和同步到数据库
        news = News()
        news.title = title
        news.digest = digest
        news.source = source
        news.content = content

        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        news.category_id = category_id
        news.user_id = user.id

        news.status = 1

        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.DBERR,errmsg='保存新闻数据失败')

        #3.6响应新闻发布的结果
        return jsonify(errno=response_code.RET.OK,errmsg='新闻发布成功')




@user_blue.route('/user_collection')
@user_login_data
def user_collection():
    '''我的收藏'''
    #1.获取用户登录信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    #2.获取参数：page
    page = request.args.get('p','1')

    #3.校验参数：是否整数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = '1'

    #4.分页查询:user.collection_news = BaseQuery类型的对象，当前第几页，每页显示几条数据
    paginate = None
    try:
        #paginate对象没有all的属性
        paginate = user.collection_news.paginate(page,constants.USER_COLLECTION_MAX_NEWS,False)
    except Exception as e:
        current_app.logger.error(e)

    #5.构造渲染模板的数据
    news_list = paginate.items
    total_page = paginate.pages
    current_page =paginate.page

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    context = {
        'news_list':news_dict_list,
        'total_page':total_page,
        'current_page':current_page
    }


    #6.渲染模板
    return render_template('news/user_collection.html',context=context)





@user_blue.route('/pass_info',methods=['GET','POST'])
@user_login_data
def pass_info():
    '''修改密码'''
    #1.获取用户登录信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    #2.请求方法为GET
    if request.method =='GET':
        return render_template('news/user_pass_info.html')

    #3.请求方法为POST的业务逻辑
    if request.method == 'POST':
        #3.1获取参数
        old_password = request.json.get('old_password')
        new_password = request.json.get('new_password')

        #3.2校验参数
        if not all([old_password,new_password]):
            return jsonify(errno=response_code.RET.PARAMERR,errmsg='缺少参数')
        #判断输入密码是否是该用户的密码
        if not user.check_password(old_password):
            return jsonify(errno=response_code.RET.PARAMERR,errmsg='原密码输入错误')

        #3.3更新到数据 password:setter方法
        user.password = new_password

        #3.4将数据同步到数据库
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.DBERR,errmsg='保存修改后的密码失败')


        #3.5响应结果
        return jsonify(errno=response_code.RET.OK,errmsg='密码修改成功')


@user_blue.route('/pic_info',methods=['GET','POST'])
@user_login_data
def pic_info():
    '''设置头像'''
    #1.获取用户登录信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    #2.实现GET请求逻辑
    if request.method == 'GET':
        #渲染模板
        context = {
            'user':user.to_dict()
        }
        #渲染界面
        return render_template('news/user_pic_info.html',context=context)
    #3.POST请求逻辑：上传用户头像
    if request.method == 'POST':
        #3.1获取参数
        avatar_file = request.files.get('avatar')

        #3.2校验参数
        try:
            avatar_data = avatar_file.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.PARAMERR,errmsg='获取头像数据失败')

        #3.3调用上传方法，将图片上传到七牛云
        try:
            key = upload_file(avatar_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.THIRDERR,errmsg='上传图片失败')

        #3.4保存到数据库
        user.avatar_url = key

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.DBERR,errmsg='保存用户头像数据失败')

        data = {
            'avatar':constants.QINIU_DOMIN_PREFIX + key
        }

        # 3.5响应头像上传结果
        return jsonify(errno=response_code.RET.OK,errmsg='头像上传成功',data=data)


@user_blue.route('/info')
@user_login_data
def user_info():
    '''个人中心入口
    提示：必须是登录用户才能进入
    '''
    #获取用户登录信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    context = {
        'user':user.to_dict()
    }
    return render_template('/news/user.html',context=context)

@user_blue.route('/base_info',methods=['GET','POST'])
@user_login_data
def base_info():
    '''基本信息'''
    #获取用户登录信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    #2.实现GET请求逻辑
    if request.method == 'GET':
        context = {
            'user': user
        }
        #渲染界面
        return render_template('news/user_base_info.html',context=context)

    #3.POST请求逻辑：修改用户基本信息
    if request.method == 'POST':
        #3.1获取参数（签名，昵称，性别）
        nick_name = request.json.get('nick_name')
        signature = request.json.get('signature')
        gender = request.json.get('gender')

        #3.2 校验参数
        if not all ([nick_name,signature,gender]):
            return jsonify(errno=response_code.RET.PARAMERR,errmsg='缺少参数')
        if gender not in ['MAN','WOMAN']:
            return jsonify(errno=response_code.RET.PARAMERR,errmsg='参数错误')

        #3.3.修改用户基本信息
        user.signature = signature
        user.nick_name = nick_name
        user.gender = gender

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.DBERR,errmsg='修改用户资料失败')

        #4.注意：修改类昵称以后，记得将状态保持信息中的昵称页修改
        session['nick_name'] = nick_name

        #5.响应修改资料的结果
        return jsonify(errno=response_code.RET.OK,errmsg='修改成功')





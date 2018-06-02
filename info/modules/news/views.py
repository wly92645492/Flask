#新闻详情，收藏，评论，点赞
from flask import abort,g,jsonify
from flask import request

from info import response_code
from info.modules import news
from info.utils.comment import user_login_data

from . import news_blue
from flask import render_template,session,current_app
from info.models import User,News, Comment
from info import constants,db
from info.utils.comment import user_login_data


# @news_blu.route('/<int:news_id>')
# @news_blue.route('/<int.news_id>')
# @user_login_data
# def news_detail(news_id):
#     ...
#     # 获取当前新闻的评论
#     click_news_list = None
#     comments = []
#     try:
#         comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
#     except Exception as e:
#         current_app.logger.error(e)
#     comment_list = []
#     for item in comments:
#         comment_dict = item.to_dict()
#         comment_list.append(comment_dict)
#
#     is_collected = False
#     # 判断用户是否收藏过该新闻
#     if g.user:
#         if news in g.user.collection_news:
#             is_collected = True
#     data = {
#         "news": news.to_dict(),
#         "click_news_list": click_news_list,
#         "is_collected": is_collected,
#         "user_info": g.user.to_dict() if g.user else None,
#         "comments": comment_list
#     }
#     return render_template('news/detail.html', data=data)


@news_blue.route('/news_comment',methods=['POST'])
@user_login_data
def news_comment():
    '''新闻评论和回复评论
    '''
    #1.获取登录用户信息
    user = g.user
    if not user:
        return jsonify(errno=response_code.RET.SESSIONERR,errmsg='用户未登录')

    #2.接收参数
    news_id = request.json.get('news_id')
    comment_content = request.json.get('comment')
    parent_id = request.json.get('parent_id')

    #3.校验参数
    if not all([news_id,comment_content]):
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='缺少参数')
    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno = response_code.RET.PARAMERR,errmsg='参数错误')

    #4.查询要评论的内容是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR,errmsg='查询新闻数据失败')
    if not news:
        return jsonify(errno=response_code.RET.NODATA,errmsg='新闻数据不存在')


    #5.实现新闻评论和回复评论逻辑
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news.id
    comment.content = comment_content

    #回复评论
    if parent_id:
        comment.parent_id = parent_id
    #同步到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR,errmsg='评论失败')


    #6.响应评论结果
    return jsonify(errno=response_code.RET.OK,errmsg='OK',data=comment.to_dict())




@news_blue.route('/news_collect',methods=['POST'])
@user_login_data
def news_collect():
    '''新闻收藏'''
    #1.获取登录用户信息
    user = g.user
    if not user:
        return jsonify(errno=response_code.RET.SESSIONERR,errmsg='用户未登录')
    # print( request.json)
    #2.接受参数（news_id)
    news_id = request.json.get('news_id')
    # print(news_id)
    action = request.json.get('action')

    #3.校验参数
    if not news_id:
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='缺少参数')
    if action not in ['collect','cancel_collect']:
        return jsonify(errno=response_code.RET.NODATA,errmsg='新闻数据不存在')


    #4.查询代收藏的新闻信息
    try:
        news = News.query.get(news_id)
        print(news)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR,errmsg='查询新闻数据失败')
    if not news:
        return jsonify(errno=response_code.RET.NODATA,errmsg='新闻数据不存在')

    #5.收藏和取消收藏
    if action == 'collect':
        #当要收藏的新闻不再用户收藏的列表中是时，才需要收藏
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        #当要取消收藏的新闻在用户收藏列表中才需要取消收藏
        if news in user.collection_news:
            user.collection_news.remove(news)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=response_code.RET.DBERR,errmsg='操作失败')

    #6.响应操作结果
    return jsonify(errno=response_code.RET.OK,errmsg='操作成功')




@news_blue.route('/detail/<int:news_id>')
@user_login_data
def news_detail(news_id):
    '''
    新闻详情
    :param news_id:要查询的新闻的id
    :return:
    1.查询登录用户的信息
    2.查询点击排行
    3.查询新闻详情
    4.累加点击量
    5.收藏和取消收藏
    '''


    # 1.查询登录用户的信息
    # user_id = session.get('user_id', None)
    # user = None
    # if user_id:
    #     # 表示用户已经登录，然后查询用户的信息
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)

    #使用函数封装获取用户信息逻辑
    # user = user_login_data()

    #从装饰器中的g变量中获取登录用户信息
    user = g.user

    # 2.新闻点击排行展示
    # news_clicks = [News,News,News,News,News,News]
    news_clicks = []
    try:
        news_clicks = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    # 3查询新闻详情
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    #后续会给404的异常准备一个友好的提示页面
    if not news:
        abort(404)

    # 4.累加点击量
    news.clicks += 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    # 5.收藏和取消收藏
    is_collected = False
    if user:
        if news in user.collection_news:
            is_collected = True

    # 如果该登录用户收藏类该新闻：is_collected


    context = {
        'user':user,
        'news_clicks':news_clicks,
        'news':news.to_dict(),
        'is_collected':is_collected
    }



    #模板渲染
    return render_template('news/detail.html',context=context)
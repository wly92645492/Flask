#新闻详情，收藏，评论，点赞
from flask import abort,g,jsonify
from flask import request
from info import response_code
from info.modules import news
from info.utils.comment import user_login_data
from flask import render_template,session,current_app
from info.models import User,News, Comment, CommentLike
from info import constants,db
from info.utils.comment import user_login_data
from . import news_blue

@news_blue.route('/followed_user', methods=['POST'])
@user_login_data
def followed_user():
    """关注和取消关注"""

    # 1.获取登录用户信息
    login_user = g.user
    if not login_user:
        return jsonify(errno=response_code.RET.SESSIONERR, errmsg='用户未登录')

    # 2.接受参数
    user_id = request.json.get('user_id')
    action = request.json.get('action')

    # 3.校验参数
    if not all([user_id,action]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
    if action not in ['follow','unfollow']:
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    # 4.查询要关注的人是否存在
    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询用户失败')
    if not other:
        return jsonify(errno=response_code.RET.NODATA, errmsg='用户不存在')

    # 5.实现关注和取消关注
    if action == 'follow':
        # 关注
        if other not in login_user.followed:
            login_user.followed.append(other)
        else:
            return jsonify(errno=response_code.RET.DATAEXIST, errmsg='已关注')
    else:
        # 取消关注
        if other in login_user.followed:
            login_user.followed.remove(other)
        else:
            return jsonify(errno=response_code.RET.DATAEXIST, errmsg='未关注')

    # 6.同步到数据库
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='保存到数据库失败')

    # 7.响应结果
    return jsonify(errno=response_code.RET.OK, errmsg='OK')

@news_blue.route('/comment_like',methods=['POST'])
@user_login_data
def comment_like():
    '''新闻点赞'''
    #1.获取用户登录信息
    user = g.user
    if not user:
        return jsonify(errno=response_code.RET.SESSIONERR,errmsg='用户未登录')

    #2.接收参数
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')

    #3.校验参数
    if not all([comment_id,action]):
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='缺少参数')
    if action not in ['add','remove']:
        return jsonify(errno=response_code.RET.PARAMERR,errmsg='参数有误')

    #4.根据客户端传入的comment_id查询出要点赞的评论
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR,errmsg='查询评论失败')
    if not comment:
        return jsonify(errno=response_code.RET.NODATA,errmsg='评论不存在')

    #5.查询要点赞的评论的是否存在，查询当前登录的用户是否给当前评论点过赞
    try:
        comment_like_model = CommentLike.query.filter(CommentLike.comment_id==comment_id,CommentLike.user_id==user.id).first()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR,errmsg='查询点赞失败')

    #6.点赞和取消点赞
    if action == 'add':
        #点赞
        if not comment_like_model:
            comment_like_model = CommentLike()
            comment_like_model.user_id = user.id
            comment_like_model.comment_id = comment_id
            #将新的记录添加到数据库
            db.session.add(comment_like_model)
            #累加点赞量
            comment.like_count +=1
            print(comment.like_count)
    else:
        #取消点赞
        if comment_like_model:
            #将记录从数据库表中删除
            db.session.delete(comment_like_model)
            #点赞数量减一
            comment.like_count -=1

    #7.同步到数据库
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR,ermsg='操作失败')

    #8.响应点赞和取消点赞
    return jsonify(errno=response_code.RET.OK,errmsg='OK')



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
    """
    新闻详情
    :param news_id: 要查询的新闻的id
    1.查询登录用户信息
    2.查询点击排行
    3.查询新闻详情
    4.累加点击量
    5.收藏和取消收藏
    6.展示用户的评论
    7.展示评论点的赞
    8.关注和取消关注
    """
    # 1.查询登录用户信息
    # 从装饰器中的g变量中获取登录用户信息
    user = g.user

    # 2.查询点击排行
    # news_clicks = [News,News,News,News,News,News]
    news_clicks = []
    try:
        news_clicks = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    # 3.查询新闻详情
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    # 后续会给404的异常准备一个友好的提示页面
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

    # 6.展示用户的评论
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id==news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    # 7.展示评论点的赞
    comment_like_ids = [] # comment_like_ids == [21,22]
    if user:
        try:
            # 查询用户点赞了哪些评论
            comment_likes = CommentLike.query.filter(CommentLike.user_id==user.id).all()
            # 取出所有被用户点赞的评论id
            comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]
        except Exception as e:
            current_app.logger.error(e)

    # 因为我希望界面渲染的数据，是经过处理的，所以我不适用模型类原始的数据，而把每个模型类转成字典to_dict()
    comment_dict_list = []
    for comment in comments:
        comment_dict = comment.to_dict()

        # 给comment_dict追加一个is_like用于记录该评论是否被登录用户点赞了
        # 14  ----  [21,22]   False
        # 15  ----  [21,22]   False ...
        # 21  ----  [21,22]   True
        # 22  ----  [21,22]   True
        comment_dict['is_like'] = False
        if comment.id in comment_like_ids:
            comment_dict['is_like'] = True

        comment_dict_list.append(comment_dict)

    # 8.关注和取消关注显示逻辑
    is_followed = False

    # 当用户已登录且登录用户正在看的新闻有作者
    # user ； 176（登录用户）
    # news.user ： 佩奇（登录用户正在看的新闻的作者）
    if user and news.user:
        # news.user ： 佩奇
        # user.followed : 176关注的人
        if news.user in user.followed:
            is_followed = True

    context = {
        # 'user':user.to_dict(),
        'user': user.to_dict() if user else None,
        'news_clicks':news_clicks,
        'news':news.to_dict(),
        'is_collected':is_collected,
        'comments':comment_dict_list,
        'is_followed':is_followed
    }

    # 渲染模板
    return render_template('news/detail.html', context=context)
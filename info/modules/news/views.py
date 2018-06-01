#新闻详情，收藏，评论，点赞
from . import news_blue
from flask import render_template

@news_blue.route('/detail/<int:news_id>')
def news_detail(news_id):
    '''
    新闻详情
    :param news_id:要查询的新闻的id
    :return:
    '''
    return render_template('news/detail.html')
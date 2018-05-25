from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect

class Config(object):
    # 开启调试模式
    DEBUGE =True
    # 配置MySql数据库链接信息：真实开发中 要使用mysql数据库的真实ip
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/information_29'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置Redis数据库:因为redis模块不是flask的扩展，所以不会自动从config中读取配置信息，只能自己读取
    REDIS_HOST = '127.0.0.1'
    REDIS_POST = '6379'

app = Flask(__name__)

# 获取配置信息
app.config.from_object(Config)

# 创建连接数据库
db = SQLAlchemy(app)

# 创建连接到redistribute数据库
redis_store = StrictRedis(host=Config.REDIS_HOST,post=Config.REDIS_POST)

# 开启csrf保护:因为项目中的表单不再使用FlaskFrom来实现，所以不会自动开启CSRF 保护，需要自己手动开启
CSRFProtect(app)

@app.route("/")
def index():
    return 'index'

if __name__ == '__main__':
    app.run()
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from config import Config

# class Config(object):
#     SECRET_KEY = 'jiangoeiha'
#     # 开启调试模式
#     DEBUGE =True
#     # 配置MySql数据库链接信息：真实开发中 要使用mysql数据库的真实ip
#     SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/information_29'
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#
#     # 配置Redis数据库:因为redis模块不是flask的扩展，所以不会自动从config中读取配置信息，只能自己读取
#     REDIS_HOST = '127.0.0.1'
#     REDIS_PORT = 6379
#
#     # 指定session使用什么来存储
#     SESSION_TYPE = 'redis'
#     # 指定session数据存储在后端的位置
#     SESSION_REDIS = StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
#     # 是否使用secret_key来签名你的数据
#     SESSION_USE_SIGNER = True
#     # 设置过期时间 要求SESSION_PERMANENT ,True 儿默认是31天
#     SESSION_PERMANENT_LIFETIME = 60 * 60 * 24



app = Flask(__name__)

# 获取配置信息
app.config.from_object(Config)

# 创建连接数据库
db = SQLAlchemy(app)

# 创建连接到redistribute数据库
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# 开启csrf保护:因为项目中的表单不再使用FlaskFrom来实现，所以不会自动开启CSRF 保护，需要自己手动开启
CSRFProtect(app)

# 指定session数据存储在后端的位置
Session(app)

# 创建脚本管理器对象
manager = Manager(app)
# 让迁移和app数据库建立管理
Migrate(app,db)
# 将数据库迁移的脚本添加到manager
manager.add_command('mysql',MigrateCommand)



@app.route("/")
def index():

    # 测试redis数据库
    # redis_store.set('name', 'lise')

    # 测试session
    from flask import session
    session['age'] = '2'

    return 'index'




if __name__ == '__main__':
    manager.run()
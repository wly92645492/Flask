
from redis import StrictRedis


class Config(object):
    SECRET_KEY = 'jiangoeiha'
    # 开启调试模式
    DEBUGE =True
    # 配置MySql数据库链接信息：真实开发中 要使用mysql数据库的真实ip
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/information_29'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置Redis数据库:因为redis模块不是flask的扩展，所以不会自动从config中读取配置信息，只能自己读取
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # 指定session使用什么来存储
    SESSION_TYPE = 'redis'
    # 指定session数据存储在后端的位置
    SESSION_REDIS = StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    # 是否使用secret_key来签名你的数据
    SESSION_USE_SIGNER = True
    # 设置过期时间 要求SESSION_PERMANENT ,True 儿默认是31天
    SESSION_PERMANENT_LIFETIME = 60 * 60 * 24

#  一下代码是封装不同开发环境下的配置信息
class DevlopmentConfig(Config):
    '''开发环境'''
    DEBUGE = True

class ProductionConfig(Config):
    '''生产环境'''
    DEBUGE = False

class UnitestConfig(Config):
    '''测试环境'''
    DEBUGE = True
    TESTING = True


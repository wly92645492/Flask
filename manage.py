from flask import Flask

class Config(object):
    # 开启调试模式
    DEBUGE =True

app = Flask(__name__)

# 获取配置信息
app.config.from_object(Config)

@app.route("/")
def index():
    return 'index'

if __name__ == '__main__':
    app.run()
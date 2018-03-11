from flask import Flask, request

app = Flask(__name__)

app.config.from_object('settings_dev')
app.config.from_envvar('ABADMIN_CONFIG', silent=True)

@app.route('/')
def hello():
    return 'hello world'


if __name__ == '__main__':
    app.run(host='0.0.0.0')

from flask import Flask, request, jsonify

app = Flask(__name__)

app.config.from_object('settings_dev')
app.config.from_envvar('ABADMIN_CONFIG', silent=True)


def return_404():
    ret = {
        'code': 0,
        'message': '',
    }
    return jsonify(ret)


@app.route('/')
def hello():
    return return_404()
    return 'hello world'


if __name__ == '__main__':
    app.run(host='0.0.0.0')

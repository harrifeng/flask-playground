# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, g, abort, make_response
from sqlite3 import dbapi2 as sqlite3
import time
import util
from flaskext.mysql import MySQL


app = Flask(__name__)
app.config.from_object('settings_dev')
app.config.from_envvar('ABADMIN_CONFIG', silent=True)

mysql = MySQL()
mysql.init_app(app)


def connect_db():
    """Connects to the specific database."""
    conn = mysql.connect()
    cursor = conn.cursor()
    return cursor


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cnt = get_db().execute(query, args)
    rv = get_db().fetchone()
    return (rv if rv else None)


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
        app.logger.info('close')

# ------------------------------------
# User
# ------------------------------------


def get_login_token(username, password):
    user = query_db('''select id, password from user where
            name = %s''', [username], one=True)
    if user is None:
        return None
    print('''[user] ==>''', user)
    if user[1] == password:
        login_timestamp = int(time.time())
        return util.create_token(user[0], login_timestamp)


# def get_user_id(username):
def get_user_id_from_token(token):
    try:
        user_id = util.parse_token(token)
        print('''[user_id] ==>''', user_id)
    except Exception:
        return None

    """Convenience method to look up the id for a username."""
    rv = query_db('select id from user where id = %s',
                  [user_id], one=True)
    return user_id if len(rv) == 1 else None


def return_404():
    ret = {
        'code': 0,
        'message': 'm',
    }
    return jsonify(ret)


def abort_with_error(code=1, message='bad request', http_code=400):
    abort(make_response(jsonify(code=code, message=message), http_code))


def gen_success_data(contents=None, total_page=1, current_page=1):
    code = 0
    message = ''
    data = []
    if contents is not None:
        data = contents
    return jsonify(code=code,
                   message=message,
                   data=data,
                   total_page=total_page,
                   current_page=current_page)


@app.route('/')
def hello():
    return 'hello world'


@app.route('/user/login', methods=['POST'])
def user_login():
    req_json = request.get_json(force=True, silent=True)
    print('''[req_json] ==>''', req_json)
    if req_json is None or 'username' not in req_json or 'password' not in req_json:
        abort_with_error('参数不足')
    token = get_login_token(req_json['username'], req_json['password'])
    print('''[token] ==>''', token)
    if token is None:
        abort_with_error('用户名或密码错误')
    else:
        return gen_success_data([{'token': token}])


@app.route('/product/list', methods=['POST'])
def product_list():
    req_json = request.get_json(force=True, silent=True)
    if req_json is None:
        abort_with_error('参数不足')
    if 'token' not in req_json or get_user_id_from_token(req_json['token']) is None:
        abort_with_error('token无效')

    return gen_success_data()


if __name__ == '__main__':
    app.run(host='0.0.0.0')

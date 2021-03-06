# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, g, abort, make_response
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
    return conn


def query_db_one(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cursor = get_db().cursor()
    cnt = cursor.execute(query, args)
    rv = cursor.fetchone()
    if cnt == 0:
        return None
    return rv


def query_db_all(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cursor = get_db().cursor()
    cnt = cursor.execute(query, args)
    rv = cursor.fetchall()
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'mysql_db'):
        g.mysql_db = connect_db()
    return g.mysql_db


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
    user = query_db_one('''select id, password from user where
            name = %s''', [username], one=True)
    if user is None:
        return None
    print('''[user] ==>''', user)
    if user[1] == password:
        login_timestamp = int(time.time())
        return util.create_token(user[0], login_timestamp)


def get_user_id_from_token(token):
    try:
        user_id = util.parse_token(token)
        print('''[user_id] ==>''', user_id)
    except Exception:
        return None

    """Convenience method to look up the id for a username."""
    rv = query_db_one('select id from user where id = %s',
                      [user_id], one=True)
    return user_id if len(rv) == 1 else None

# ------------------------------------
# Layer
# ------------------------------------


def get_unused_segments(layer_id):
    groups = query_db_all('''select segments from exp_group where status=1
    and layer_id = %s and end_time > %s ''', [layer_id, util.get_datetime_str(0)])
    total = [True] * 1000
    print('''[groups] ==>''', groups)
    for group in groups:
        segs = group[0].split(',')
        for seg in segs:
            if seg.isdigit():
                index = int(seg) % 1000
            else:
                index = 0
            total[index] = False
    return [str(i) for i in range(1000) if total[i]]


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
    if req_json is None or 'username' not in req_json or 'password' not in req_json:
        abort_with_error('参数不足')
    token = get_login_token(req_json['username'], req_json['password'])
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

    products = query_db_all('''select id, cname, ename, level from product''')

    data = []
    for product in products:
        data.append({
            'id': product[0],
            'cname': product[1],
            'ename': product[2],
            'level': product[3],
        })

    return gen_success_data(data)


@app.route('/layer/add', methods=['POST'])
def layer_add():
    req_json = request.get_json(force=True, silent=True)
    if req_json is None or 'product_id' not in req_json or 'name' not in req_json:
        abort_with_error('参数不足')
    if 'token' not in req_json or get_user_id_from_token(req_json['token']) is None:
        abort_with_error('token无效')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''insert into layer(name, status, product_id, params, create_time,
    update_time) values (%s, %s, %s, %s, %s, %s)''', [req_json['name'], 1,
                                                      req_json['product_id'],
                                                      req_json.get('params'),
                                                      util.get_datetime_str(),
                                                      util.get_datetime_str()])
    db.commit()
    return gen_success_data([{'id': cursor.lastrowid}])


@app.route('/layer/close', methods=['POST'])
def layer_close():
    req_json = request.get_json(force=True, silent=True)
    if req_json is None or 'layer_id' not in req_json:
        abort_with_error('参数不足')
    if 'token' not in req_json or get_user_id_from_token(req_json['token']) is None:
        abort_with_error('token无效')
    db = get_db()
    cursor = db.cursor()
    row = cursor.execute('''update layer set status=%s where id=%s''', [
                         2, req_json['layer_id']])
    db.commit()
    return gen_success_data([{'id': req_json['layer_id']}])


@app.route('/layer/list', methods=['POST'])
def layer_list():
    req_json = request.get_json(force=True, silent=True)
    if req_json is None:
        abort_with_error('参数不足')
    if 'token' not in req_json or get_user_id_from_token(req_json['token']) is None:
        abort_with_error('token无效')

    product_id = req_json.get('product_id', 0)
    if product_id > 0:
        layers = query_db_all('''select id, name, create_time from layer where product_id=%s''',
                              [product_id])
    else:
        layers = query_db_all('''select id, name, create_time from layer''')

    data = []
    for layer in layers:
        data.append({
            'id': layer[0],
            'name': layer[1],
            'create_time': util.get_str_from_datetime(layer[2])
        })

    return gen_success_data(data)


@app.route('/layer/traffic', methods=['POST'])
def layer_traffic():
    req_json = request.get_json(force=True, silent=True)
    if req_json is None or 'layer_id' not in req_json:
        abort_with_error('参数不足')
    if 'token' not in req_json or get_user_id_from_token(req_json['token']) is None:
        abort_with_error('token无效')

    layer_id = req_json['layer_id']
    groups = query_db_all('''select segment_num from exp_group where layer_id=%s and
        status = 1 and end_time > %s''', [layer_id, util.get_datetime_str(0)])

    rest = 1000 - sum(group[0] for group in groups)
    data = [{'segment': rest}]
    return gen_success_data(data)


@app.route('/group/add_one', methods=['POST'])
def group_add_one():
    req_json = request.get_json(force=True, silent=True)
    if (req_json is None or 'layer_id' not in req_json or
                'name' not in req_json or
                'segment' not in req_json or
            'filter' not in req_json or
            'end_time' not in req_json
            ):
        abort_with_error('参数不足')
    if 'token' not in req_json or get_user_id_from_token(req_json['token']) is None:
        abort_with_error('token无效')

    unused_segments = get_unused_segments(req_json['layer_id'])
    segment_num = req_json['segment']
    if len(unused_segments) < segment_num:
        abort_with_error('segment余量不足')

    # db = get_db()
    # cursor = db.cursor()
    # cursor.execute('''insert into group(name, status, product_id, params, create_time,
    # update_time) values (%s, %s, %s, %s, %s, %s)''', [req_json['name'], 1,
    #                                                   req_json['product_id'],
    #                                                   req_json.get('params'),
    #                                                   util.get_datetime_str(),
    #                                                   util.get_datetime_str()])
    # db.commit()
    # return gen_success_data([{'id': cursor.lastrowid}])


    data = []
    return gen_success_data(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0')

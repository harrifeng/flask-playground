# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, g, abort, make_response
from sqlite3 import dbapi2 as sqlite3

app = Flask(__name__)

app.config.from_object('settings_dev')
app.config.from_envvar('ABADMIN_CONFIG', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = query_db('select id from user where name = ?',
                  [username], one=True)
    return rv[0] if rv else None


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


# @app.route('/users')
# def user():
#     id = get_user_id('fan')
#     return gen_success_data([{'id': id, 'user': 'usera'}])

@app.route('/user/login', methods=['POST'])
def user():
    req_json = request.get_json(force=True, silent=True)
    print('''[req_json] ==>''', req_json)
    if req_json is None or 'username' not in req_json or 'password' not in req_json:
        abort_with_error('参数不足')
    id = get_user_id('fan')
    return gen_success_data([{'id': id, 'user': 'usera'}])


if __name__ == '__main__':
    app.run(host='0.0.0.0')

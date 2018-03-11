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


@app.route('/')
def hello():
    db = get_db()
    abort_with_error()
    return 'hello world'


if __name__ == '__main__':
    app.run(host='0.0.0.0')

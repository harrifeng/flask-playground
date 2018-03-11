# -*- coding: utf-8 -*-
import base64
import hashlib
import datetime

token_salt = "ilove$==abtest"
FORMAT_STR = '%Y-%m-%d %H:%M:%S'


def get_datetime_and_str(delta_days=0, fmt=FORMAT_STR):
    now = datetime.datetime.now()
    want = now + datetime.timedelta(days=delta_days)
    return (want, want.strftime(fmt))


def get_datetime_str(delta_days=0, fmt=FORMAT_STR):
    now = datetime.datetime.now()
    want = now + datetime.timedelta(days=delta_days)
    return want.strftime(fmt)


def get_datetime_from_str(date_str, fmt=FORMAT_STR, def_date=None):
    try:
        if len(date_str) == 0:
            return None
        ret = datetime.datetime.strptime(date_str, fmt)
    except ValueError as ex:
        print('''[ex] ==>''', ex)
        return None
    return ret


def get_str_from_datetime(datetm, fmt=FORMAT_STR):
    return datetm.strftime(fmt)


def md5(estr):
    hl = hashlib.md5()
    hl.update(estr.encode(encoding='utf-8'))
    mstr = hl.hexdigest()
    return mstr


def create_token(user_id, login_timestamp):
    """
    创建token
    """
    mstr = md5(token_salt)
    key = "%s:%d:%d" % (mstr, user_id, login_timestamp)
    return base64.b64encode(key)


def parse_token(token):
    """
    解析token
    """
    dstr = base64.b64decode(token)
    mstr, user_id, login_timestamp = dstr.split(":")
    cmstr = md5(token_salt)

    # 判定salt正确性
    if mstr != cmstr:
        return False
    # token时效性 TODO

    return user_id

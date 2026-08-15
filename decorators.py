from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def owner_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('user_type') != 'owner':
            flash('Owner access required.')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return wrapper

from flask import Flask, request, session, g, abort, render_template, url_for, flash, redirect
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, send, emit
from flask_github import GitHub
from flask_session import Session
from threading import Thread
from queue import Queue
import argparse
import json
import math
import os

from ..common.database import Database
from ..docker.listener import MessageListener


def setup_app_routes(app, github, socketio, debug):

    @app.before_request
    def before_request():
        g.user = None
        if '_id' in session:
            g.user = Database().user(session['_id'])

    @app.route('/login')
    def login():
        if session.get('_id', None) is None:
            return github.authorize(scope='user')
        else:
            return "Already logged in"

    @app.route('/logout')
    def logout():
        session['_id'] = None
        return redirect('/')

    @app.route('/github-callback')
    @github.authorized_handler
    def authorized(oauth_token):
        next_url = request.args.get('next') or url_for('index')
        if oauth_token is None:
            flash("Authorization failed.")
            return redirect(next_url)

        user = Database().user_by_oauth(oauth_token)
        if user is None:
            g.user = {'oauth': oauth_token}

            github_user = github.get('/user')
            if not Database().update_oauth(github_user['id'], oauth_token):
                flash("Authorization failed.")
                return redirect(next_url)

            user = Database().user_by_oauth(oauth_token)

        g.user = user
        session['_id'] = user['_id']
        return redirect(next_url)

    @github.access_token_getter
    def token_getter():
        user = g.user
        if user is not None:
            return user['oauth']
        return None
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @socketio.on('is-logged')
    def is_user_logged():
        before_request()

        if debug and g.user is None:
            emit('login-status', {'_id': 0, 'username': 'debug-username'})
        else:
            emit('login-status', g.user)

    @socketio.on('fetch-instances')
    def fetch_instances():
        before_request()
        if g.user is None:
            emit('user-instances', [])
        else:
            emit('user-instances', Database().user_instances(g.user['_id']))


def listener(messages):
    results = MessageListener('rabbit', 'jobs', messages)
    results.run()

def main():
    parser = argparse.ArgumentParser(description='Classroom AutoGrader')
    parser.add_argument('--github-client-id', help='Github client id for logins')
    parser.add_argument('--github-client-secret', help='Github client secret for logins')
    parser.add_argument('--mongo-host', default='mongo', help='MongoDB hostname')
    parser.add_argument('--host', type=str, default='localhost', help='Server hostname')
    parser.add_argument('--port', type=int, default=80, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Run server in debug mode')    
    args = parser.parse_args()

    # Start database
    Database.initialize(args.mongo_host)

    # TODO(gpascualg): Move this somewhere else
    messages = Queue()
    thread = Thread(target=listener, args=(messages,))
    thread.start()

    app = Flask(__name__)
    app.config['GITHUB_CLIENT_ID'] = args.github_client_id
    app.config['GITHUB_CLIENT_SECRET'] = args.github_client_secret
    app.config['SESSION_TYPE'] = 'mongodb'
    app.config['SESSION_MONGODB'] = Database().client
    app.config['CORS_HEADERS'] = 'Content-Type'

    dir_path = os.path.dirname(os.path.realpath(__file__))
    app.config['STATIC_FOLDER'] = os.path.join(dir_path, 'static')

    CORS(app)
    Session(app)
    socketio = SocketIO(app, manage_session=False)
    github = GitHub(app)

    setup_app_routes(app, github, socketio, args.debug)
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)
    thread.join()
    
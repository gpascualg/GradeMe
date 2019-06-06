from servers.common.redisbc import RedisBC
from flask import Flask
from flask import request
from threading import Thread
import threading
from flask import copy_current_request_context
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit
from flask_socketio import join_room, leave_room
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
clients = []


#emit('status', {'msg': session.get('name') + ' has entered the room.'}, room=clients[0])

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)


@app.route('/')
def hello_world():
    return render_template('index.html',  async_mode=socketio.async_mode)

@socketio.on('connect')
def on_connect():
    print('FLASK APP: new user connected')
    emit('my_response', 'asdssssss', namespace='/test')
    emit('newMsg', {'data': 'Connected'})
    
@socketio.on('message', namespace='/test')
def on_message():
    print('ssssssssssssssssssssssssssssssssss')
    
@socketio.on('qwe', namespace='/test')
def test_message(message):
    print('message received')

@socketio.on('join')
def on_join(data):
    print('client joined')
    username = data['username']
    room = data['room']
    clients.append(room)
    join_room(room)
    send(username + ' has entered the room.', room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', room=room)
    
def asd(msg):
    #socketio.emit('newMsg', {'data': msg}, namespace='/test')
    socketio.emit('newMsg', str(msg), namespace='/test')
    #socketio.emit('newMsg', {'data': msg})
    #socketio.send('asd', namespace='/test')
    #socketio.send('asd')
    print('callback received from redis'+str(msg))
    
if __name__ == '__main__':
    print('qweqweqwe')
    
    with app.app_context():
        RedisBC().connect("redis",6379)
        RedisBC().subscribe(asd,"hola")
    socketio.run(app, host='0.0.0.0', debug=True)
    
    
    #try:
     #   RedisBC().connect("localhost",6379)
      #  RedisBC().subscribe(cb,"hola")
    #except Exception as e:
     #   print(e)
    #print("debug")
    #app.run(debug=True,host='0.0.0.0')
    #print("fin debug")
    
    
    
    

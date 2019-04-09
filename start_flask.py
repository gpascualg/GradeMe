from servers.common.redisbc import RedisBC
from flask import Flask
from flask import request
app = Flask(__name__)
#qweqweqweqweasdasdasd
@app.route('/')
def hello_world():
    return "<p>FUNCIONA</p>"
    

@app.route('/q')
def q():
    username = request.args.get('username')
    password = request.args.get('password')
    toret = "<p>Q</p>"
    toret = toret + "<p>"
    toret = toret + str(username)
    toret = toret + "</p><p>"
    toret = toret + str(password)
    toret = toret + "</p>"
    return toret
    

@app.route('/w')
def w():
    return "<p>W</p>"    
    
def cb(asd):
    print(asd)
    return asd
    
if __name__ == '__main__':
    try:
        RedisBC().connect("localhost",6379)
        RedisBC().subscribe(cb,"hola")
    except Exception as e:
        print(e)
    print("debug")
    app.run(debug=True,host='0.0.0.0')
    print("fin debug")
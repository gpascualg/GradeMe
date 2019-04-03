import redis
from flask import Flask
app = Flask(__name__)
#qweqweqweqweasdasdasd
@app.route('/')
def hello_world():
    return 'Flask Dockerized'

if __name__ == '__main__':
    print("eheheheheh")
    app.run(debug=True,host='0.0.0.0')
    print("eheheheheh")
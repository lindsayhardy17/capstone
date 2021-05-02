from os import environ
from flask import Flask
app = Flask(__name__)
#host = "0.0.0.0";
#port = environ.get("PORT", 17995);


@app.route('/')
def hello_world():
    print("hello world")
    return 'i hope this works'
    
if __name__ == "__main__":
    port = int(environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

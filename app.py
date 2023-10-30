from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
#import analizador.grammar as g

from interpretar import *

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methos": [
    "GET", "POST", "PUT", "DELETE"], "headers": "Authorization"}})

last_response = None

@app.route("/", methods=['GET'])
def inicio():
    return("Hola Mundo")

@app.route("/comandos", methods=['POST'])
def comandos():
    global last_response
    comandos = request.data.decode().replace("\\n", "\n").replace("\"", "").replace("\\", "")
    response = jsonify(ejecutar(comandos))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route("/logs", methods=['POST'])
def credenciales():
    global last_response
    c = request.data.decode().replace("\\n", "\n").replace("\"", "").replace("\\", "")
    t, r = interpretar_comando(c)
    response = jsonify({"mensaje":t.strip("\n")})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route("/hola", methods=['GET'])
def hola():
    return "Hola a Todos!!"

if __name__ == '__main__':
    app.run(debug=True, port=4000, host='0.0.0.0')
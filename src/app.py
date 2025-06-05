from flask import Flask, request, jsonify
from flask_cors import CORS
from answer import answer

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/question', methods=['POST'])
def question():
    data = request.json
    response = {
        "answer": answer(data.get("question", ""))
    }
    return response, 200

@app.route('/')
def root():
    return "hi" , 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8081)
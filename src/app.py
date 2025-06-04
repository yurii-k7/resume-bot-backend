from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/question', methods=['POST'])
def question():
    data = request.json
    return jsonify(data), 200

if __name__ == '__main__':
    app.run(port=8081)
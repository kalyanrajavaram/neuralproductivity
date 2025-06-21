from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

@app.route("/api/data", methods=["GET"])
def get_data():
    return jsonify({"message": "Hello from Flask!"})

@app.route("/api/submit", methods=["POST"])
def submit_data():
    data = request.json
    return jsonify({"received": data})

if __name__ == "__main__":
    app.run(port=5000, debug=True)

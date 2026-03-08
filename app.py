from flask import Flask, jsonify, request

app = Flask(__name__)

members = [
    {"id": 1, "name": "Rahul", "plan": "Premium"},
    {"id": 2, "name": "Anita", "plan": "Basic"}
]

@app.route('/')
def home():
    return "Welcome to ACEest Fitness & Gym"

@app.route('/members')
def get_members():
    return jsonify(members)

@app.route('/members', methods=['POST'])
def add_member():
    data = request.get_json()
    members.append(data)
    return {"message": "Member added"}, 201

@app.route('/health')
def health():
    return {"status": "running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
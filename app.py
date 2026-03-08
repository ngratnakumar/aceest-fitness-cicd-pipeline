from flask import Flask, jsonify, request

app = Flask(__name__)

members = [
    {"id": 1, "name": "Rahul", "plan": "Premium"},
    {"id": 2, "name": "Anita", "plan": "Basic"}
]

trainers = [
    {"id": 1, "name": "Vikram", "specialization": "Strength"},
    {"id": 2, "name": "Sara", "specialization": "Yoga"}
]


@app.route('/')
def home():
    return "Welcome to ACEest Fitness & Gym Management System"


@app.route('/members', methods=['GET'])
def get_members():
    return jsonify(members)


@app.route('/members', methods=['POST'])
def add_member():
    data = request.get_json()
    members.append(data)
    return jsonify({"message": "Member added successfully"}), 201


@app.route('/trainers')
def get_trainers():
    return jsonify(trainers)


@app.route('/health')
def health():
    return {"status": "running"}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
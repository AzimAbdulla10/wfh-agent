from flask import Flask, request

app = Flask(__name__)

@app.route("/checkin", methods=["POST"])
def checkin():
    print("CHECKIN RECEIVED")
    print(request.json)
    return {"status": "success"}

@app.route("/checkout", methods=["POST"])
def checkout():
    print("CHECKOUT RECEIVED")
    print(request.json)
    return {"status": "success"}

app.run(host="0.0.0.0", port=5000)

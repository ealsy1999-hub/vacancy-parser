from flask import Flask, send_file
import subprocess
import os

app = Flask(__name__)

@app.route("/")
def index():
    if not os.path.exists("data/dashboard.html"):
        subprocess.run(["python", "src/bulk_parser.py"])
        subprocess.run(["python", "src/build_dashboard.py"])
    return send_file("data/dashboard.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, jsonify, request, send_file, render_template, send_from_directory, redirect, url_for, flash
#from flask_toastr import Toastr
from collections import deque
import time
import os
import psutil
import requests
import socket

app = Flask(__name__)

    
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


lock_get_file = False
lock_load_file = True
lock_status = False

password = r"YOURPASSHERE"



@app.route("/", methods=["HEAD"])
def head():
    return (
        jsonify({"message": "Hello, world"}),
        200,
        {"Content-Type": "application/json"},
    )


@app.route("/", methods=["GET"])
def index():
    #filenames = os.listdir(app.config['UPLOAD_FOLDER'])
    filenames = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', filenames=filenames), 200, {"Content-Type": "text/html"}


'''@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("favicon.ico")
'''

@app.route("/<filename>")
def get_file(filename):
    if os.path.isfile(os.path.join("files", filename)):
        return (
            open(os.path.join("files", filename), "r").read(),
            200,
            {"Content-Type": "application/json"},
        )
    for node in nodes:
        try:
            response = requests.get(f"{node}/{filename}", params={"key": password})
            if response.status_code == 200:
                return response.content, 200, {"Content-Type": "application/json"}
        except:
            continue
    return (
        jsonify({"error": "File not found"}),
        404,
        {"Content-Type": "application/json"},
    )


@app.route("/upload", methods=["POST"])
def load_file():
    if 'file' not in request.files:
        return "Incorrect name"
    file = request.files['file']
    if file.filename == '':
        return "File was not chosen"
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        path = os.path.join(request.base_url, file.filename)           
        file.save(filename)
        return redirect('/')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/status", methods=["GET"])
def status():
    if lock_status and request.args.get("key") != password:
        return (
            jsonify({"error": "Access denied"}),
            403,
            {"Content-Type": "application/json"},
        )
    usage = psutil.disk_usage("/")
    free_space = int(usage.free / 1024)
    return jsonify({"free_space": free_space})

'''
@app.route("/config", methods=["GET"])
def config():
    return jsonify(
        {
            "lock_get_file": lock_get_file,
            "lock_load_file": lock_load_file,
            "lock_status": lock_status,
        }
    )
'''
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok = True)
    app.run(host='0.0.0.0')

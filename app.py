from flask import Flask, jsonify, request, send_file, render_template, send_from_directory, redirect, url_for, flash
from collections import deque
import time
import os
import psutil
import requests
import socket
from minio import Minio
from dotenv import load_dotenv
from urllib.request import urlopen

load_dotenv()

LOCAL_FILE_PATH = os.environ.get('LOCAL_FILE_PATH')
ACCESS_KEY = os.environ.get('ACCESS_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
MINIO_API_HOST = "http://localhost:9000"

MINIO_CLIENT = Minio("localhost:9000", access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)

app = Flask(__name__)

if not os.path.exists("files"):
    os.makedirs("files")
    
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
    objects = MINIO_CLIENT.list_objects('mybucket', prefix=None, recursive = True)
    filenames = [object.object_name for object in objects]
    get_bucket_files()
    return render_template('index.html', filenames=filenames), 200, {"Content-Type": "text/html"}


@app.route("/upload", methods=["POST"])
def load_file():
    if 'file' not in request.files:
        return "Incorrect name"
    file = request.files['file']
    if file.filename == '':
        return "File was not chosen"
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        MINIO_CLIENT.fput_object("mybucket", file.filename, filename, file.mimetype)
        os.remove(filename)
        return redirect('/')
 

def get_bucket_files():
        #try:
        objects = MINIO_CLIENT.list_objects('mybucket', prefix=None, recursive = True) # prefix The object name prefix for filtering
        for obj in objects:
            print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
                  obj.etag, obj.size, obj.content_type)
        #except ResponseError as err:
        #    print(err)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    res = MINIO_CLIENT.fget_object("mybucket", filename, filename)
    url = MINIO_CLIENT.get_presigned_url(
    "GET",
    "mybucket",
    filename,
    )
    opened_url =  urlopen(url)
    return send_file(opened_url, mimetype=res.content_type)


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

@app.route('/delete/<filename>', methods=['POST', 'GET'])
def delete_file(filename):
    #try:
    MINIO_CLIENT.remove_object('mybucket', filename)
    print('Object removed successfully')
    return redirect(url_for('index'))
    #except ResponseError as err:
    #    print(err)
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

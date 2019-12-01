from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse
import werkzeug
import boto3
from uuid import uuid4
from settings import *
from tempfile import TemporaryFile

import os
import hashlib

app = Flask(__name__)
api = Api(app)

def s3Upload(fh, name):
    if DEBUG: # save locally
        with open(name, "wb") as f:
            f.write(fh.read())
        fh.seek(0, os.SEEK_SET)

    try:
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        s3.upload_fileobj(fh, bucket, name)
        fh.close()
        return {}
    except Exception as e:
        print(e)
        return {"error": "failed to upload to s3"}

def md5(fh):
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: fh.read(4096), b""):
        hash_md5.update(chunk)
    fh.seek(0, os.SEEK_SET) # reset position to beginning of file
    return hash_md5.hexdigest()

""" xor the first 256 bytes of provided file with XOR_KEY,
and return a new temporary file with the decrypted data """
def undo_xor(fh):
    t = TemporaryFile("r+b")
    fh.seek(0, os.SEEK_SET) # reset position to beginning of file
    xor_region = [b ^ XOR_KEY for b in fh.read(256)]
    normal_region = fh.read()
    data = bytes(xor_region) + bytes(normal_region)
    t.write(data)
    t.seek(0, os.SEEK_SET)
    fh.close()
    return t

class Server(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        parser.add_argument('checksum')
        args = parser.parse_args()

        file_upload = args.get('file')
        checksum = args.get('checksum')
        # TODO: error code(s) for client interpretation, not 200, rather Bad Request, etc.
        if checksum is None:
            print("checksum parameter not in request")
            return {"error" : "checksum parameter not in request"}
        elif file_upload is None:
            print("file parameter not in request")
            return {"error" : "file parameter not in request"}
        elif checksum != md5(file_upload):
            print("file upload checksum mismatch")
            return {"error": "file upload checksum mismatch"}
        print(file_upload.filename)
        name = ''.join([str(uuid4().hex[:6]) + "-", file_upload.filename])
        file_upload = undo_xor(file_upload)

        return s3Upload(file_upload, name)

api.add_resource(Server, "/server")

if __name__ == '__main__':
    app.run(debug=DEBUG)

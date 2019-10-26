from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse
import werkzeug
import boto3
from uuid import uuid4

#delete this before commit
AWS_ACCESS_KEY_ID = #insert id here
AWS_SECRET_ACCESS_KEY = #insert key here
bucket = #insert bucket here

app = Flask(__name__)
api = Api(app)

def s3Upload(file):
    try:
        filename = file.filename
        random_file_name = ''.join([str(uuid4().hex[:6]) + "-", filename])
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        s3.upload_fileobj(file, bucket, random_file_name)
        return {"data":filename}
    except Exception as e:
        print(e)
        return {"error": e}



class server(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parser.parse_args()
        file = args['file']
        return s3Upload(file)

api.add_resource(server, "/server")

if __name__ == '__main__':
    app.run(debug=True)
from locust import HttpLocust, TaskSet, task
import sys, os, base64, datetime, hashlib, hmac 
import requests
import json


json_obj = [
    {

    },
	{

	}]
json_str = json.dumps(json_obj)

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def getSignatureKey(key, date_stamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning


# Read AWS access key from env. variables or configuration file. Best practice is NOT
# to embed credentials in code.
access_key = '<access_key>'
secret_key = '<secret_key>'
if access_key is None or secret_key is None:
    print('No access key is available.')
    sys.exit()

# Create a date for headers and the credential string
method = 'POST'
service = 'sagemaker'
host = 'runtime.sagemaker.eu-west-1.amazonaws.com'
region = 'eu-west-1'
canonical_uri = '<URI>'
canonical_querystring = ''
signed_headers = 'content-type;host;x-amz-date'
payload_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
algorithm = 'AWS4-HMAC-SHA256'
content_type = 'application/json'

class UserBehavior(TaskSet):

    def on_start(self):
        self.client.verify = False

    @task(1)
    def predict(self):
        t = datetime.datetime.utcnow()
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope
        canonical_headers = 'content-type:' + content_type + '\n' + 'host:' + host + '\n' + 'x-amz-date:' + amz_date + '\n'
        canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
        credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
        string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        signing_key = getSignatureKey(secret_key, date_stamp, region, service)
        signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
        authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
        headers = {'Content-Type':content_type,
                    'X-Amz-Date':amz_date,
                    'Authorization':authorization_header}
        self.client.post(canonical_uri,
                    json_str,
                    headers=headers)

class EndpointUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 500
    max_wait = 2000
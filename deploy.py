REGISTRY = '836736564967.dkr.ecr.us-east-2.amazonaws.com/tbp'
REGION = 'us-east-2'
FUNCTION_NAME = 'tbp'

import os, subprocess
import boto3
client = boto3.client('lambda', region_name=REGION)

os.system('docker build -t tbp .')
os.system('aws ecr get-login-password --region {} | docker login --username AWS --password-stdin {}'.format(REGION, REGISTRY))
os.system('docker tag tbp {}'.format(REGISTRY))
result = subprocess.run(['docker', 'push', REGISTRY], stdout=subprocess.PIPE)
output = result.stdout.decode('utf-8')
output = output.split('\n')
output = [l for l in output if len(l.strip()) > 0]
lastline = output[-1].split(' ')
signature = lastline[2]
uri = '{}@{}'.format(REGISTRY, signature)
client.update_function_code(
  FunctionName=FUNCTION_NAME,
  ImageUri=uri
)

print('Deploying:', uri)
waiter = client.get_waiter('function_updated')
waiter.wait(FunctionName=FUNCTION_NAME)

res = client.publish_version(FunctionName=FUNCTION_NAME)
client.update_alias(
  FunctionName=FUNCTION_NAME,
  Name='prod',
  FunctionVersion=res['Version']
)

print('Successfully deployed.')

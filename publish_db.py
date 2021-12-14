REGISTRY = '836736564967.dkr.ecr.us-east-2.amazonaws.com/tbp-postgres'
REGION = 'us-east-2'

DB_URL = 'postgresql://postgres:postgres@localhost:5432/tbp-dev'

import os

os.system('npx pg-anonymizer {} '
          '--list=password,phone:734-442-2888,comments:faker.random.words,'
          'answer=faker.random.words,language_barrier:faker.datatype.boolean'.format(DB_URL))

with open('output.sql', 'r+') as f:
  content = f.read()
  f.seek(0, 0)
  f.write('CREATE ROLE tbp_django\n'
          'LOGIN\n'
          "PASSWORD 'postgres';\n"
          'ALTER USER tbp_django CREATEDB;\n' + content)

os.system('docker build -t tbp-postgres -f Dockerfile.postgres .')
os.system('aws ecr get-login-password --region {} | docker login --username AWS --password-stdin {}'.format(REGION, REGISTRY))
os.system('docker tag tbp-postgres {}'.format(REGISTRY))
os.system('docker push {}'.format(REGISTRY))

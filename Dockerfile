FROM public.ecr.aws/lambda/python:2.7
  
WORKDIR ${LAMBDA_TASK_ROOT}

RUN yum -y install freetype-devel libpng-devel gcc gcc-c++
RUN yum -y install python27-devel.x86_64
RUN yum -y install libjpeg-devel

COPY requirements.txt .
RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
RUN python get-pip.py

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir djangoajax==2.2.12 Django==1.9 gunicorn==0.17.0
RUN pip install --no-cache-dir numpy==1.16.6
RUN pip install --no-cache-dir apig_wsgi

COPY . .

CMD [ "migweb.wsgi.lambda_handler" ]

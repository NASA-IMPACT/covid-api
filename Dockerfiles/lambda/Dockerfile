FROM lambci/lambda:build-python3.7


# We install covid_api and mangum
WORKDIR /app

COPY README.md /app/README.md
COPY covid_api/ /app/covid_api/
COPY setup.py /app/setup.py

RUN pip install --upgrade pip
RUN pip install . "mangum==0.9.2" -t /var/task --no-binary numpy, pydantic

# Reduce package size and remove useless files
RUN cd /var/task && find . -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[2-3][0-9]//'); cp $f $n; done;
RUN cd /var/task && find . -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN cd /var/task && find . -type f -a -name '*.py' -print0 | xargs -0 rm -f
RUN find /var/task -type d -a -name 'tests' -print0 | xargs -0 rm -rf
RUN echo "Remove lambda python packages"
RUN rm -rdf /var/task/numpy/doc/ 
RUN rm -rdf /var/task/stack
RUN rm -rdf /var/task/boto3*
RUN rm -rdf /var/task/botocore*
RUN rm -rdf /var/task/docutils*
RUN rm -rdf /var/task/dateutil*
RUN rm -rdf /var/task/jmespath*
RUN rm -rdf /var/task/s3transfer*


COPY lambda/handler.py /var/task/handler.py


FROM lambci/lambda:build-python3.7


# We install covid_api and mangum
WORKDIR /app

COPY README.md /app/README.md
COPY covid_api/ /app/covid_api/
COPY setup.py /app/setup.py

RUN pip install --upgrade pip
RUN pip install . "mangum>=0.9.0" -t /var/task --no-binary numpy, pydantic

# Reduce package size and remove useless files
RUN cd /var/task && find . -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[2-3][0-9]//'); cp $f $n; done;
RUN cd /var/task && find . -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN cd /var/task && find . -type f -a -name '*.py' -print0 | xargs -0 rm -f
RUN find /var/task -type d -a -name 'tests' -print0 | xargs -0 rm -rf
RUN rm -rdf /var/task/numpy/doc/
RUN rm -rdf /var/task/stack


COPY lambda/handler.py /var/task/handler.py


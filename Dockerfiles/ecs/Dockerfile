FROM tiangolo/uvicorn-gunicorn:python3.8
# Ref https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker/issues/15
# Cuts image size by 50%
# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt
RUN sed -i 's/DEFAULT@SECLEVEL=2/DEFAULT@SECLEVEL=1/' /etc/ssl/openssl.cnf

COPY README.md /app/README.md
COPY covid_api/ /app/covid_api/
COPY setup.py /app/setup.py
RUN mkdir /app/stack
COPY stack/config.yml /app/stack/config.yml

RUN pip install -e /app/. --no-cache-dir

CMD ["/start-reload.sh"]

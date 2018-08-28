FROM python:3-alpine3.6
RUN pip install pyyaml
COPY sync.py ./
ENTRYPOINT [ "python", "sync.py" ]

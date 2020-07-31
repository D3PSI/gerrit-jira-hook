FROM openfrontier/gerrit-ci
RUN apk add python3 \
        py3-pip
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt

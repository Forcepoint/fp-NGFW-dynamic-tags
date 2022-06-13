FROM python:3.9-slim-buster

COPY requirements.txt /

RUN pip install --no-cache-dir --upgrade -r /requirements.txt

WORKDIR /app
COPY ./main.py /
RUN chmod +x /main.py

ENTRYPOINT ["python", "/main.py"]


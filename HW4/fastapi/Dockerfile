FROM python:3.13-slim

WORKDIR /fastapi

COPY * ./

RUN pip install -r requirements.txt

RUN playwright install --with-deps chromium

EXPOSE 8000

CMD fastapi run extract_save_data.py --host=0.0.0.0 --port=8000

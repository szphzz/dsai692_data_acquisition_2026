FROM python:3.13-slim

WORKDIR /HW3-Assigned

COPY * ./

RUN pip install -r requirements.txt

EXPOSE 8501

CMD streamlit run streamlit/hw3.py --server.address 0.0.0.0
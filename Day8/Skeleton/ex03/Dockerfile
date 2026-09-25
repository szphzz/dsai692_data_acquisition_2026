# Use python:3.13-slim as a base image 
FROM python:3.13-slim

# Set /Day8 as a working directory
WORKDIR /Day8

COPY * ./

# Install libraries and packages
RUN pip install -r requirements.txt

# expose port 8501, which is the default port for streamlit
EXPOSE 8501

#Run streamlit application
CMD streamlit run main.py --server.address 0.0.0.0
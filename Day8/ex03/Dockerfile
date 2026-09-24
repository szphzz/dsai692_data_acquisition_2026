# Use python:3.13-slim as a base image 
FROM python:3.13-slim

# Set /Day8 as a working directory
WORKDIR /Day8

# Copy environment.yml
COPY * .

# Install required packages/libs
RUN pip install -r requirements.txt

# #xpose port 8501
EXPOSE 8501

# Run streamlit
CMD ["streamlit", "run", "main.py", "--server.address", "0.0.0.0"]
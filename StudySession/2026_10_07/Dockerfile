# base image should be should python:3-13
FROM python:3-13
# set the working dir as /example1
WORKDIR /example1
# copy all .ipynb files from the current local dir to image
# Assume you're running `docker build .` insdie 2026_10_07 dir
COPY *.ipynb /example1
# /example1/studysession.ipynb will be placed
# copy all .py files from the current local dir to image
COPY *.py .
# pip install numpy
RUN pip install numpy

# WORKDIR /example3 # mkdir /example3, cd /example3
# run streamlit ex01.py as an entry point 
CMD streamlit run ex01.py


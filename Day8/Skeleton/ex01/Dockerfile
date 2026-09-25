# Use python:3.13-slim as a base image 
FROM python:3.13-slim

# Set /Day8 as a working directory in the container
 WORKDIR /Day8

# Copy everything in the working directory (in your local machine) to /Day8 in the container
# make sure to run docker build in the dir you want to copy, can include path below if want to
# this should copy requirements.txt and ex01.py
COPY * .

# Install packages and libraries
# this runs within the image (not locally)
RUN pip install -r requirements.txt

# expose port 8000
EXPOSE 8000

# run the ex01.py as fastapi server.
# if there are multiple CMDs, only the last one will run
CMD fastapi run ex01.py --port=8000

# also works, just a diff way of formatting
# CMD ["fastapi", "run", "ex01.py", "--port=8000"]

# docker must be running
# docker build -t day8_ex01 .  # looks for Dockerfile in curr dir
# the image is not running at this point, just built
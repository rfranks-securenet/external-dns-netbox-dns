# Use an official lightweight Python image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

RUN chmod 0777 /tmp

# Copy project files into the container
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

EXPOSE 8888
EXPOSE 8080

# Command to run the app
#CMD [ "gunicorn", "--no-control-socket", "-b", "[::]:8888", "-b", "[::]:8080", "--access-logfile", "-", "--error-logfile", "-", "main:app" ]
CMD [ "gunicorn", "--no-control-socket", "-b", "[::]:8888", "-b", "[::]:8080", "--error-logfile", "-", "main:app" ]
#CMD [ "python", "main.py" ]

# Pull the base image
FROM tiangolo/uwsgi-nginx-flask:python3.9
# Install depndencies 
RUN pip install Flask
RUN pip install opencensus-ext-azure
RUN pip install opencensus-ext-flask
RUN pip install redis
RUN pip install opencensus
RUN pip install opencensus-ext-logging
RUN pip install applicationinsights
RUN pip install prometheus_flask_exporter
# Copy the content of the current directory to the /app of the container
ADD . /app

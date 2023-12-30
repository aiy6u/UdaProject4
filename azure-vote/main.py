from flask import Flask, request, render_template
import os
import random
import redis
import socket
import logging
from datetime import datetime

# Azure Application Insights
from applicationinsights import TelemetryClient
from opencensus.ext.azure import metrics_exporter, trace_exporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Application Insights
insights_cnn_str = "InstrumentationKey=8cd17a87-3ec5-4339-8f75-15051ca4f220;IngestionEndpoint=https://westus2-2.in.applicationinsights.azure.com/;LiveEndpoint=https://westus2.livediagnostics.monitor.azure.com/"

# Metrics
exporter = metrics_exporter.new_metrics_exporter(enable_standard_metrics=True, connection_string=insights_cnn_str)

# Tracing
tracer = Tracer(
    exporter=AzureExporter(connection_string=insights_cnn_str),
    sampler=ProbabilitySampler(rate=1.0),
)

# Flask Middleware for Tracing

app = Flask(__name__)

# Flask Middleware for Tracing
middleware = FlaskMiddleware(app, exporter=exporter)

# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if "VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']:
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if "VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']:
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if "TITLE" in os.environ and os.environ['TITLE']:
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Redis Connection
redis_url = "redis://default:2tBGOciIrItDZvyxFueKEhQlTAvMOVhX@redis-17695.c53.west-us.azure.cloud.redislabs.com:17695"
r = redis.StrictRedis.from_url(redis_url)

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1):
    r.set(button1, 0)
if not r.get(button2):
    r.set(button2, 0)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        # Get current values
        vote1 = r.get(button1).decode('utf-8')
        # Tracing: use tracer object to trace cat vote
        tracer.span(name="CatVoteSpan").add_attribute("VoteValue", vote1)
        
        vote2 = r.get(button2).decode('utf-8')
        # Tracing: use tracer object to trace dog vote
        tracer.span(name="DogVoteSpan").add_attribute("VoteValue", vote2)

        # Return index with values
        return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

    elif request.method == 'POST':
        if request.form['vote'] == 'reset':
            # Empty table and return results
            r.set(button1, 0)
            r.set(button2, 0)
            vote1 = r.get(button1).decode('utf-8')
            # Logging: use logger object to log cat vote
            logger.info("Cat vote reset: %s", vote1)

            vote2 = r.get(button2).decode('utf-8')
            # Logging: use logger object to log dog vote
            logger.info("Dog vote reset: %s", vote2)

            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)
        else:
            # Insert vote result into DB
            vote = request.form['vote']
            r.incr(vote, 1)

            # Get current values
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')

            # Return results
            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

if __name__ == "__main__":
    # Use the statement below when running locally
    #app.run()
    # Use the statement below before deployment to VMSS
    app.run(host='0.0.0.0', threaded=True, debug=True)  # remote

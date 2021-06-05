from flask import Flask, request, render_template
import os
import random
import redis
import socket
import sys
import logging
from datetime import datetime
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from applicationinsights.flask.ext import AppInsights
from opencensus.ext.azure.log_exporter import AzureEventHandler
from applicationinsights import TelemetryClient

APPINSIGHTS_INSTRUMENTATIONKEY = "InstrumentationKey=c156d48a-c3c4-47f9-b8af-c1ba2e4675d6;IngestionEndpoint=https://westus2-2.in.applicationinsights.azure.com/"

app = Flask(__name__)


logger = logging.getLogger(__name__)
logger.addHandler(AzureEventHandler(connection_string = APPINSIGHTS_INSTRUMENTATIONKEY))
logger.setLevel(logging.INFO)

# Metrics
#exporter = # TODO: Setup exporter
exporter = metrics_exporter.new_metrics_exporter(enable_standard_metrics=True,connection_string=APPINSIGHTS_INSTRUMENTATIONKEY)


# Tracing
#tracer = # TODO: Setup tracer
tracer = TelemetryClient(APPINSIGHTS_INSTRUMENTATIONKEY)



# Requests
#middleware = # TODO: Setup flask middleware
middleware = FlaskMiddleware(app,exporter=AzureExporter(connection_string=APPINSIGHTS_INSTRUMENTATIONKEY),sampler=ProbabilitySampler(rate=1.0),)


# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if ("VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']):
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if ("VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']):
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if ("TITLE" in os.environ and os.environ['TITLE']):
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Redis Connection
r = redis.Redis()

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1): r.set(button1,0)
if not r.get(button2): r.set(button2,0)

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':

        # Get current values
        vote1 = r.get(button1).decode('utf-8')
        # TODO: use tracer object to trace cat vote
        tracer.track_event("Cat Votes")
        tracer.flush()
        vote2 = r.get(button2).decode('utf-8')
        # TODO: use tracer object to trace dog vote
        tracer.track_event("Dog Votes")
        tracer.flush()

        # Return index with values
        return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

    elif request.method == 'POST':

        if request.form['vote'] == 'reset':

            # Empty table and return results
            r.set(button1,0)
            r.set(button2,0)
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')
            # TODO: use logger object to log cat vote
            properties = {'custom_dimensions': {'Cat Votes': vote1}}
            logger.warning("Cat Votes",extra=properties)
            # TODO: use logger object to log dog vote
            properties = {'custom_dimensions': {'Dog Votes': vote2}}
            logger.warning("Dog Votes",extra=properties)

            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

        else:

            # Insert vote result into DB
            vote = request.form['vote']
            r.incr(vote,1)

            # Get current values
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')

            # TODO: use logger object to log cat vote
            properties = {'custom_dimensions': {'Cat Votes': vote1}}
            logger.warning("Cat Votes",extra=properties)
            # TODO: use logger object to log dog vote
            properties = {'custom_dimensions': {'Dog Votes': vote2}}
            logger.warning("Dog Votes",extra=properties)

            # Return results
            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

if __name__ == "__main__":

    app.run()

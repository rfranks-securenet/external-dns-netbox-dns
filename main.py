"""
Main entry point for the External DNS Netbox DNS webhook plugin
"""
#!/usr/bin/env python3

import os
import logging

from flask import Flask
from flask_restful import Api

import pynetbox

from resources.DomainFilter import DomainFilter
from resources.Records import Records
from resources.Health import Health
from resources.AdjustEndpoints import AdjustEndpoints

import Cache

logging.basicConfig(level=logging.DEBUG)

Cache.test_connection()

app = Flask(__name__)
app.debug = True
api = Api(app)

api.add_resource(DomainFilter, '/')
api.add_resource(Records, '/records')
api.add_resource(Health, '/healthz')
api.add_resource(AdjustEndpoints, '/adjustendpoints')

if __name__ == '__main__':
    app.run(debug=True)

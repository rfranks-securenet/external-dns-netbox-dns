"""
Domain Filter resource
"""

import os
import json
import logging

from flask_restful import Resource
from flask import Response

import Cache


class DomainFilter(Resource):
    """ Resource for returning the domain filter """
    def get(self):
        """ Handle a get request """
        logging.debug("Running DomainFilter")
        allowed_zones = os.getenv("DOMAIN_FILTERS", "")
        zonelist = []
        zones = Cache.controller.zoneList.zones
        for name in allowed_zones.split(","):
            try:
                zone = zones[name]
                if zone.active:
                    zonelist.append(zone.name)
            except KeyError:
                pass
        return Response(json.dumps({'filters': zonelist}), status=200, mimetype='application/external.dns.webhook+json;version=1')

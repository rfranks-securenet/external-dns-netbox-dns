"""
Adjust endpoints
"""

import os
import json
import logging

from flask_restful import Resource
from flask import request, Response

import Cache

logger = logging.getLogger(__name__)


class AdjustEndpoints(Resource):
    """Resource for returning adjusted endpoints"""

    def post(self):
        """Handle a post request"""

        logger.debug("Running adjustendpoints")
        body = json.loads(request.data)
        return Response(
            json.dumps(body),
            status=200,
            mimetype="application/external.dns.webhook+json;version=1",
        )

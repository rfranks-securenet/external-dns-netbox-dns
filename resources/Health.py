"""
Healthz resource controller
"""

from flask_restful import Resource
import Cache

class Health(Resource):
    """ Resource for returning the current plugin health """
    def get(self):
        """ Handle GET request """
        try:
            Cache.controller.recordList.records
        except Exception as e:
            print(dir(e))
            return {"message": "Could not connect to backend"}, 500
        return {"status": "ok"}, 200

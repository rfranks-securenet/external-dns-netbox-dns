"""
Records list controller
"""
import json
import logging

from flask_restful import Resource
from flask import request, Response

import Cache

logger = logging.getLogger(__name__)


class NetboxBackendException(Exception):
    """Exception with the Netbox backend"""


class InvalidDataException(Exception):
    """Invalid data passed into the request"""


class Records(Resource):
    """Resource controller for Records"""

    def get(self):
        """Handle a GET request"""
        logger.debug("Running GET records")
        recordlist = []
        records = Cache.controller.recordList.records
        for key in records:
            record = records[key]
            recordlist.append(
                {
                    "dnsName": record.fqdn.rstrip("."),
                    "recordType": record.type,
                    #'setIdentifier': 'v1',
                    "recordTTL": record.ttl,
                    "targets": [record.value],
                }
            )
        logger.debug("Returning %s records", len(recordlist))
        logger.debug("Returning records: %s", recordlist)
        return Response(
            json.dumps(recordlist),
            status=200,
            mimetype="application/external.dns.webhook+json;version=1",
        )

    def _processCreate(self, createCommands) -> (list, list):
        """Process the 'create' commands"""
        zones = Cache.controller.zoneList.zones
        records = Cache.controller.recordList.records

        logging.debug("Existing records: %s", records)

        to_create = []
        to_overwrite = []
        logger.debug("Processing create records")

        for record in createCommands:
            logger.debug("Processing %s", record["dnsName"])
            for target in record["targets"]:
                found = False
                fqdn = record["dnsName"]
                record_type = record["recordType"]
                subdomain = fqdn[fqdn.find(".") + 1 :]

                # First check if this is an update from Netbox's point of view
                try:
                    nb_record = records[f"{fqdn}${record_type}${target}"]
                    this_record = {
                        "id": nb_record.id,
                        "zone": nb_record.zone.id,
                        "name": nb_record.name,
                        "type": record_type,
                        "value": target,
                        "ttl": record.get("recordTTL", 3600),
                    }
                    logger.debug(
                        "Processing %s as an update to netbox", record["dnsName"]
                    )
                    to_overwrite.append(this_record)
                    continue
                except KeyError:
                    logger.debug("Not an update - process as a create")
                    # This isn't an update from netbox's point of view, so must be a create
                    while not found:
                        try:
                            zones[subdomain]
                            found = True
                        except KeyError:
                            if subdomain.find(".") == -1:
                                # Not found
                                logging.warning(
                                    "Could not find a domain for record %s", fqdn
                                )
                                raise NetboxBackendException(
                                    f"Domain not found for record {fqdn}"
                                )
                            subdomain = subdomain[subdomain.find(".") + 1 :]
                    this_record = {
                        "zone": zones[subdomain].id,
                        "name": record["dnsName"][: -len(subdomain) - 1],
                        "type": record["recordType"],
                        "value": target,
                        "ttl": record.get("recordTTL", 3600),
                    }
                    to_create.append(this_record)
        return to_create, to_overwrite

    def _processDelete(self, deleteCommands) -> list:
        """Process the 'delete' commands"""
        logger.debug("Processing delete commands: %s", deleteCommands)
        records = Cache.controller.recordList.records
        to_delete = []
        for record in deleteCommands:
            fqdn = record["dnsName"]
            recordType = record["recordType"]
            for target in record["targets"]:
                try:
                    to_delete.append(records[f"{fqdn}${recordType}${target}"].id)
                except KeyError:
                    raise NetboxBackendException(
                        f"Could not delete non-existant record: {fqdn}"
                    )
        return to_delete

    def _processUpdate(self, old: list, new: list) -> list:
        """Process the 'update' commands"""
        logger.debug("Processing update commands: %s", old)
        records = Cache.controller.recordList.records
        to_update = []
        if not len(old) == len(new):
            raise InvalidDataException(
                "updateOld and updateNew are of different lengths"
            )
        for i in range(len(old)):
            old_record = old[i]
            new_record = new[i]
            if not len(old_record["targets"]) == len(new_record["targets"]):
                raise InvalidDataException(
                    f"Targets of different lengths in {old_record['dnsName']}"
                )
            fqdn = old_record["dnsName"]
            record_type = old_record["recordType"]
            for j in range(len(old_record["targets"])):
                target = old_record["targets"][j]
                try:
                    nb_old_record = records[f"{fqdn}${record_type}${target}"]
                except KeyError:
                    raise NetboxBackendException(
                        f"Could not find existing record {fqdn}"
                    )
                this_record = {
                    "id": nb_old_record.id,
                    "zone": nb_old_record.zone.id,
                    "name": new_record["dnsName"][: -len(nb_old_record.zone.name) - 1],
                    "type": new_record["recordType"],
                    "value": new_record["targets"][j],
                    "ttl": new_record["recordTTL"],
                }
                to_update.append(this_record)
        return to_update

    def post(self):
        """Handle a POST request"""
        body = json.loads(request.data)

        logger.debug("Got post: %s", body)

        to_create = []
        to_overwrite = []
        to_delete = []
        to_update = []

        try:
            to_delete = self._processDelete(body.get("delete", []))
        except NetboxBackendException as e:
            logging.warn("Unable to process deletion")
            return {"message": e.args[0]}, 500
        logger.debug("Processing deletes: %s", to_delete)
        for delete in to_delete:
            Cache.controller.recordList.deleteRecord(delete)

        try:
            to_create, to_overwrite = self._processCreate(body.get("create", []))
        except NetboxBackendException as e:
            logging.warn("Unable to process creation")
            return {"message": e.args[0]}, 500
        logger.debug("Processing creates: %s", to_create)
        Cache.controller.recordList.createRecord(to_create)
        logger.debug("Processing overwrites: %s", to_overwrite)
        for update in to_overwrite:
            Cache.controller.recordList.updateRecord(update["id"], update)

        try:
            to_update = self._processUpdate(
                body.get("updateOld", []), body.get("updateNew", [])
            )
        except NetboxBackendException as e:
            logging.warn("Unable to process updates")
            return {"message": e.args[0]}, 500
        except InvalidDataException as e:
            logging.warn("Invalid data on updates")
            return {"message": e.args[0]}, 500

        logger.debug("Processing updates: %s", to_update)
        for update in to_update:
            Cache.controller.recordList.updateRecord(update["id"], update)

        return Response(
            json.dumps({}),
            status=200,
            mimetype="application/external.dns.webhook+json;version=1",
        )

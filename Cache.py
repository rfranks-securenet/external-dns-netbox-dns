"""
Cache controller for accessing the backend Netbox instance
"""

from datetime import datetime, timedelta
import os
import logging

import pynetbox
import requests
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)


def test_connection():
    class TimeoutHTTPAdapter(HTTPAdapter):
        def __init__(self, *args, **kwargs):
            self.timeout = kwargs.get("timeout", 5)
            super().__init__(*args, **kwargs)

        def send(self, request, **kwargs):
            kwargs["timeout"] = self.timeout
            return super().send(request, **kwargs)

    adapter = TimeoutHTTPAdapter()
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.verify = False

    nb = pynetbox.api(os.getenv("NETBOX_URL"), token=os.getenv("NETBOX_TOKEN"))
    nb.http_session = session

    logger.debug("Testing connection to netbox")
    try:
        nb.status()
        logger.debug("Connection to netbox ok")
    except requests.exceptions.ConnectionError as e:
        logger.error(
            "Unable to connect to the netbox instance: %s", os.getenv("NETBOX_URL")
        )
        logger.error(e)
        exit(1)
    except requests.exceptions.TimeoutError as e:
        logger.error(
            "Timeout connecting to netbox instance: %s", os.getenv("NETBOX_URL")
        )
        exit(1)
    except pynetbox.core.query.RequestError as e:
        logger.error("Netbox backend error")
        exit(1)


class ZoneList:
    """List of Zone objects from Netbox"""

    _zones: dict
    _nb: object
    _refreshTime: datetime
    _ttl: int

    def __init__(self, nb, ttl):
        self._ttl = ttl
        self._refreshTime = datetime(1970, 1, 1)
        self._nb = nb

    def _needsRefresh(self) -> bool:
        """Whether or not the cache is stale"""
        now = datetime.now()
        return now > self._refreshTime + timedelta(seconds=self._ttl)

    def _forceRefresh(self):
        """Force a refresh of the cache contents"""
        nbzones = self._nb.plugins.netbox_dns.zones.all()
        self._zones = {}
        for zone in nbzones:
            self._zones[zone.name] = zone
            self._refreshTime = datetime.now()

    def _refresh(self):
        """Refresh if needed"""
        if not self._needsRefresh():
            return
        self._forceRefresh()

    @property
    def zones(self):
        """Zones that are held in this list"""
        self._refresh()
        return self._zones

    def healthy(self):
        """Whether this list is healthy"""
        try:
            self._forceRefresh()
            return True
        except Exception:
            return False


class RecordList:
    """List of record objects from Netbox"""

    _records: dict
    _nb: object
    _refreshTime: datetime
    _ttl: int

    def __init__(self, nb, ttl):
        self._ttl = ttl
        self._refreshTime = datetime(1970, 1, 1)
        self._nb = nb

    def _needsRefresh(self) -> bool:
        """Whether or not the cache is stale"""
        now = datetime.now()
        return now > self._refreshTime + timedelta(seconds=self._ttl)

    def _forceRefresh(self):
        """Force a refresh of the cache contents"""
        nbrecords = self._nb.plugins.netbox_dns.records.filter(
            active=True, managed=False
        )
        self._records = {}
        for record in nbrecords:
            self._records[
                f"{record.name}.{record.zone.name.rstrip('.')}${record.type}${record.value}"
            ] = record
            self._refreshTime = datetime.now()

    def _refresh(self):
        """Refresh if needed"""
        if not self._needsRefresh():
            return
        self._forceRefresh()

    @property
    def records(self):
        """Records that are held in this list"""
        self._refresh()
        return self._records

    def createRecord(self, records: list):
        """Add a record to Netbox"""
        self._nb.plugins.netbox_dns.records.create(records)
        self._forceRefresh()

    def updateRecord(self, recordId, updates):
        """Update a record in Netbox"""
        record = self._nb.plugins.netbox_dns.records.get(recordId)
        record.update(updates)
        self._forceRefresh()

    def deleteRecord(self, recordId):
        """Delete a record from Netbox"""
        record = self._nb.plugins.netbox_dns.records.get(recordId)
        record.delete()
        self._forceRefresh()

    def healthy(self):
        """Whether this list is healthy"""
        try:
            self._forceRefresh()
            return True
        except Exception:
            return False


class CacheController:
    """Cache controller to hold the individual list caches"""

    _zones: ZoneList
    _records: RecordList

    def __init__(self, ttl: int = 120):
        logger.debug("Initialising CacheController")
        netbox_url = os.getenv("NETBOX_URL", "")
        netbox_token = os.getenv("NETBOX_TOKEN", "")
        nb = pynetbox.api(netbox_url, token=netbox_token)
        self._zones = ZoneList(nb, ttl)
        self._records = RecordList(nb, ttl)

    @property
    def zoneList(self):
        """Cached Zone List object"""
        return self._zones

    @property
    def recordList(self):
        """Cached Record List object"""
        return self._records


controller = CacheController()

import os
import pynetbox
import requests

nb = pynetbox.api(os.getenv("NETBOX_URL"), token=os.getenv("NETBOX_TOKEN"))

try:
    nb.status()
    print("Status ok")
except requests.exceptions.ConnectionError as e:
    print("Connection error to upstream")
except pynetbox.core.query.RequestError as e:
    print("Netbox error")

# External DNS netbox dns
This is an external-dns webhook plugin to update the [Netbox DNS](https://github.com/sys4/netbox-plugin-dns) plugin

## Environment variables
The following environment variables should be used for the pod:

| Name | Description |
|------|-------------|
| DOMAIN_FILTERS | Comma separated list of domains that should be considered as part of the plugin |
| NETBOX_URL | URL for reaching the netbox instance |
| NETBOX_TOKEN | Netbox token for accessing the API |

You must also make sure that there is a writable temporary directory, for example an emptydir mounted at /tmp

An example addition to the external-dns helm `values.yml` is shown below


```yaml
extraVolumes:
  - name: tmpfs
    emptyDir: {}
provider:
  name: webhook
  webhook:
    image:
      repository: ghcr.io/sncs-uk/external-dns-netbox-dns
      tag: latest
      pullPolicy: Always
    env:
      - name: DOMAIN_FILTERS
        value: example.com
      - name: NETBOX_URL
        value: http://netbox.example.com
      - name: NETBOX_TOKEN
        value: nbt_SuperSecretAPIToken
    extraVolumeMounts:
      - name: tmpfs
        mountPath: /tmp
        readOnly: false
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL
      privileged: false
      readOnlyRootFilesystem: true
      runAsGroup: 65532
      runAsNonRoot: true
      runAsUser: 65532
policy: sync
managedRecordTypes:
  - A
  - AAAA
  - CNAME
  - PTR
resources:
  limits:
    cpu: "200m"
    memory: "128Mi"
  requests:
    cpu: "100m"
    memory: "64Mi"
sources:
  - "service"
  - "ingress"
  - "crd"
  - "gateway-httproute"
```

import base64
import json
def encode(oid):
    enc = str(base64.b64encode(bytes(str(oid), 'latin-1')))
    enc = enc[2 : len(enc)-1]
    return oid

def decode(id):
    res=base64.b64decode(id).decode('latin-1')
    return id
import hashlib

def compute_checksum(data):
    return hashlib.sha256(data).hexdigest()
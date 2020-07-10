import os
import hashlib
import struct
import camellia


#
# https://github.com/mon/sv3c_decrypt/
#

def xor(data, key):
    data = bytearray(data)
    key = bytearray(key)
    for i in range(len(data)):
        data[i] ^= key[i]
    return data


def generate_keys(path):
    salt = "5dIFp5Nb8n1kyPRSU8dKGyhJHx317PA3"
    key_offsets = [8, 25, 22, 47, 24,  5, 16,  9, 33,  3, 45,  1, 30, 34, 37, 36,
                   15, 39, 11, 14, 23, 29, 26, 40, 31,  7, 13, 38, 27, 17, 12, 21]
    iv_offsets = [28, 19, 2,  46, 4,  20, 18, 41, 32, 43, 0,  6,  44, 10, 35, 42]
    filename = os.path.basename(path)

    to_hash = salt + filename + salt + filename
    hashed = bytes(hashlib.sha384(to_hash.encode("ASCII")).digest())
    key = [0] * 32
    for offset, i in zip(key_offsets, range(32)):
        key[i] = hashed[offset]

    iv = bytearray([0]*16)
    for offset, i in zip(iv_offsets, range(16)):
        iv[i] = hashed[offset]
    iv = bytes(iv)

    iv = struct.unpack("<Q", iv[:8])[0] | (struct.unpack("<Q", iv[8:])[0] << 64)

    return key, iv


def obfuscate(path):
    salt = "[oh6|}:?rTf5*8zS"
    strip = ["data", "./data", "/data"]
    for s in strip:
        if path.startswith(s):
            path = path[len(s):]

    to_hash = salt + path
    hashed = hashlib.md5(to_hash.encode("ASCII")).hexdigest()
    return "data/{}/{}/{}/{}".format(hashed[0], hashed[1], hashed[2], hashed[3:])


class CamelliaCounter:
    def __init__(self, iv):
        self.counter = 0
        self.iv = iv
        self.commonKey = 0x53856E750D645467AE91F2FF0FA28735

    def next(self):
        ctr = self.counter * self.commonKey
        self.counter += 1
        ret = self.iv + ctr
        mask = 0xFFFFFFFFFFFFFFFF  # 64 bit
        return struct.pack("<2Q", ret & mask, (ret >> 64) & mask)

    def next_bytes(self, count):
        ret = (self.next() for _ in range((count+15) // 16))
        return b"".join(ret)


def crypt_file(source, key, iv):
    key = bytes(bytearray(key))

    with open(source, "rb") as src:
        crypt = src.read()

    ctr = CamelliaCounter(iv)
    cam = camellia.CamelliaCipher(key=key, mode=camellia.MODE_ECB)
    # generate the entire key at once since bigger inputs run faster
    key_stream = cam.encrypt(ctr.next_bytes(len(crypt)))

    return xor(crypt, key_stream)


def decrypt_file(source_dir, path):
    key, iv = generate_keys(path)
    ob = obfuscate(path)
    return crypt_file(os.path.join(source_dir, ob), key, iv)

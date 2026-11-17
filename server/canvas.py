"""Look up Spotify Canvas video URLs (unofficial, uses the sp_dc cookie).

The web-player token endpoint needs a TOTP built from a secret Spotify rotates;
we pull the current secret from a community-maintained feed and fall back to a
built-in copy if the feed is down.
"""
import base64
import hashlib
import hmac
import struct
import time

import requests

TOKEN_URL = "https://open.spotify.com/api/token"
CANVAS_URL = "https://spclient.wg.spotify.com/canvaz-cache/v0/canvases"
SECRETS_URL = "https://code.thetadev.de/ThetaDev/spotify-secrets/raw/branch/main/secrets/secretDict.json"
FALLBACK_SECRETS = {"61": [44, 55, 47, 42, 70, 40, 34, 114, 76, 74, 50, 111, 120, 97, 75, 76, 94, 102, 43, 69, 49, 120, 118, 80, 64, 78]}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


# ---------- TOTP ----------
def _latest_secret():
    try:
        secrets = requests.get(SECRETS_URL, timeout=5).json()
    except Exception:
        secrets = FALLBACK_SECRETS
    version = max(secrets, key=int)
    return version, secrets[version]


def _totp(cipher_bytes, t=None):
    transformed = [b ^ ((i % 33) + 9) for i, b in enumerate(cipher_bytes)]
    key = "".join(str(n) for n in transformed).encode()
    counter = int((t or time.time()) // 30)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{code:06d}"


# ---------- minimal protobuf ----------
def _varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _read_varint(buf, pos):
    shift = result = 0
    while True:
        b = buf[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, pos
        shift += 7


def _field(num, payload):
    return _varint((num << 3) | 2) + _varint(len(payload)) + payload


def _parse(buf):
    """Return list of (field_number, bytes) for length-delimited fields; skip others."""
    pos, fields = 0, []
    while pos < len(buf):
        key, pos = _read_varint(buf, pos)
        num, wtype = key >> 3, key & 7
        if wtype == 2:
            ln, pos = _read_varint(buf, pos)
            fields.append((num, buf[pos:pos + ln])); pos += ln
        elif wtype == 0:
            _, pos = _read_varint(buf, pos)
        elif wtype == 1:
            pos += 8
        elif wtype == 5:
            pos += 4
        else:
            break
    return fields


# ---------- client ----------
class CanvasClient:
    def __init__(self, sp_dc):
        self.sp_dc = sp_dc
        self.token = None
        self.expires = 0

    def _refresh_token(self):
        version, cipher = _latest_secret()
        code = _totp(cipher)
        r = requests.get(TOKEN_URL, params={
            "reason": "init", "productType": "web-player",
            "totp": code, "totpServer": code, "totpVer": version,
        }, cookies={"sp_dc": self.sp_dc}, headers={"User-Agent": UA}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data.get("accessToken"):
            raise RuntimeError(f"no accessToken in response: {data}")
        self.token = data["accessToken"]
        self.expires = data.get("accessTokenExpirationTimestampMs", 0) / 1000 - 60

    def _token(self):
        if not self.token or time.time() > self.expires:
            self._refresh_token()
        return self.token

    def canvas_url(self, track_id):
        """Return the Canvas mp4 URL for a track id, or None if the track has no Canvas."""
        body = _field(1, _field(1, f"spotify:track:{track_id}".encode()))
        r = requests.post(CANVAS_URL, data=body, headers={
            "Authorization": f"Bearer {self._token()}",
            "Content-Type": "application/x-protobuf",
            "Accept": "application/protobuf",
            "User-Agent": UA,
        }, timeout=10)
        if r.status_code == 401:
            self.token = None
            return self.canvas_url(track_id)
        r.raise_for_status()
        for num, canvas in _parse(r.content):
            if num != 1:
                continue
            for fnum, val in _parse(canvas):
                if fnum == 2 and val.endswith(b".mp4"):
                    return val.decode()
        return None


if __name__ == "__main__":
    import os, sys
    from dotenv import load_dotenv
    load_dotenv()
    c = CanvasClient(os.environ["SP_DC"])
    for tid in sys.argv[1:] or ["3OHfY25tqY28d16oZczHc8"]:
        print(tid, "->", c.canvas_url(tid))

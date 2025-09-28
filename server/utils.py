# utils.py
import socket, secrets, time
import dns.resolver

SERVER_IP = "13.49.221.83"   # <-- YOUR SERVER PUBLIC IP

def is_valid_hostname(hostname: str) -> bool:
    # Basic safe regex; adjust as needed
    import re
    return bool(re.match(r"^[a-zA-Z0-9\-\.*]{1,253}$", hostname))

def resolves_to_server(domain: str) -> bool:
    """
    Returns True if any A/CNAME resolution chain yields SERVER_IP.
    Works when client sets A record or CNAME -> a host that resolves to SERVER_IP.
    """
    try:
        # gethostbyname_ex follows CNAMEs to A records
        ips = socket.gethostbyname_ex(domain)[2]
        return SERVER_IP in ips
    except Exception:
        return False

def generate_token() -> str:
    # short, safe token for TXT verification
    return secrets.token_urlsafe(16)

def check_txt_record(domain: str, token: str, prefix="_verify") -> bool:
    """
    Check TXT at _verify.DOMAIN (so name in DNS UI: _verify or _verify.domain).
    """
    try:
        answers = dns.resolver.resolve(f"{prefix}.{domain}", "TXT")
        for rdata in answers:
            txt = "".join(rdata.strings) if hasattr(rdata, "strings") else rdata.to_text()
            # dnspython returns bytes in .strings; safe compare
            if token in txt or token in str(txt):
                return True
    except Exception:
        return False
    return False

def poll_txt(domain: str, token: str, timeout=600, interval=10) -> bool:
    """
    Poll for TXT token until found or timeout seconds elapsed.
    """
    end = time.time() + timeout
    while time.time() < end:
        if check_txt_record(domain, token):
            return True
        time.sleep(interval)
    return False

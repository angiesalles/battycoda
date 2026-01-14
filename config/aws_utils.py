"""
AWS IP discovery utilities
"""

import urllib.request


def get_public_ip():
    """Get the public IP address using Amazon's checkip service

    Returns:
        str: Public IP address or None if not available
    """
    public_ip = None

    try:
        # Get public IP from Amazon's checkip service
        checkip_url = "http://checkip.amazonaws.com"
        public_ip_response = urllib.request.urlopen(checkip_url, timeout=2.0).read()
        public_ip = public_ip_response.decode("utf-8").strip()
    except Exception as e:
        print(f"Error getting public IP: {str(e)}")

    return public_ip

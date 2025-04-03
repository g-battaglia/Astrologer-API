import socket
import struct
from typing import Union
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_ntp_time(server: str = "time.google.com", timeout: int = 5) -> Union[datetime, Exception]:
    """
    Gets the current time from an NTP server.
    
    Args:
        server: The NTP server to use (default: time.google.com)
        timeout: The connection timeout in seconds (default: 5)
    
    Returns:
        A datetime object in UTC timezone representing the current time or raises an exception
    """
    NTP_PORT = 123
    # RFC 4330 format - Mode: 3 (client), Version: 3
    NTP_PACKET = b'\x1b' + 47 * b'\0'
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(NTP_PACKET, (server, NTP_PORT))
            data, _ = sock.recvfrom(48)
            
            # Extract the timestamp (second field Transmit Timestamp)
            # RFC 4330: bytes 40-47 contain the Transmit Timestamp
            transmit_time = struct.unpack('!II', data[40:48])
            
            # The first value represents seconds since 1900-01-01
            ntp_seconds = transmit_time[0]
            
            # Convert from NTP epoch (1900) to Unix epoch (1970)
            unix_time = ntp_seconds - 2208988800
            
            # Return a datetime object with UTC timezone
            return datetime.fromtimestamp(unix_time, tz=timezone.utc)
            
    except socket.timeout as e:
        logger.error(f"Timeout error: {e}")
        raise TimeoutError("Timeout during NTP request") from e
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e

if __name__ == "__main__":
    # Example usage
    try:
        ntp_time = get_ntp_time()
        print(f"Current NTP time: {ntp_time}")
    except Exception as e:
        print(f"Failed to get NTP time: {e}")
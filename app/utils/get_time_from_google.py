import requests
from datetime import datetime

def get_time_from_google():
    response = requests.head("https://www.google.com")
    date_header = response.headers.get("Date")
    
    if date_header:
        # Converti la stringa della data in un oggetto datetime
        return datetime.strptime(date_header, "%a, %d %b %Y %H:%M:%S GMT")
    else:
        raise ValueError("Header 'Date' not found in the response.")

if __name__ == "__main__":
    current_time = get_time_from_google()
    print("Ora corrente da Google:", current_time)
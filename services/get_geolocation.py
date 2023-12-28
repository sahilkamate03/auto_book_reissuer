import requests

def get_geolocation(ip_address):
    url = 'https://freegeoip.app/json/' + ip_address
    response = requests.get(url)
    data = response.json()
    if data:
        return data['country_name'], data['region_name'], data['city']
    else:
        return None, None, None
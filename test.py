import requests

# Define the proxy server address and port
PROXY_SERVER = 'http://<ip>:<port>'

# Define the URLs to request
urls = [
    "https://www.youtube.com/@ddatunashvili/videos"
]

def make_request(url):
    try:

        proxies = {
            'http': PROXY_SERVER,
            'https': PROXY_SERVER,
        }

        response = requests.get(url, proxies=proxies)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"URL: {url}")
        print(f"Status Code: {response.status_code}")

    except requests.RequestException as e:
        print(f"Error occurred while requesting {url}: {e}")


if __name__ == "__main__":
    for url in urls:
        make_request(url)

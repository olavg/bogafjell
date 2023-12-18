from waybackpy import WaybackMachineAvailabilityAPI
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse

def is_valid_url(url, base_domain):
    parsed = urlparse(url)
    return bool(parsed.netloc) and parsed.netloc.endswith(base_domain)

def download_file(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.basename(urlparse(url).path)
            if not filename or '.' not in filename:
                filename = "index.html"
            file_path = os.path.join(folder, filename)

            # Detect encoding
            encoding = response.encoding if response.encoding else 'utf-8'

            with open(file_path, 'w', encoding=encoding) as file:
                file.write(response.text)  # Use response.text to correctly handle encoding
            return file_path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None

def crawl_page(url, base_domain, folder, visited):
    if url in visited:
        return

    print(f"Crawling: {url}")
    visited.add(url)
    page_content = download_file(url, folder)

    if not page_content:
        return

    # Parse with correct encoding
    soup = BeautifulSoup(open(page_content, encoding='utf-8'), 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href']
        joined_url = urljoin(url, href)
        if is_valid_url(joined_url, base_domain) and joined_url not in visited:
            crawl_page(joined_url, base_domain, folder, visited)

def download_site(url, user_agent, folder, year, month, day, hour):
    # Initialize the Availability API and find the snapshot near the specified date
    availability_api = WaybackMachineAvailabilityAPI(url, user_agent)
    nearest_snapshot = availability_api.near(year=year, month=month, day=day, hour=hour)

    if nearest_snapshot:
        archive_url = nearest_snapshot.archive_url
        print("Nearest Archived URL:", archive_url)

        # Make directories for downloaded files
        os.makedirs(folder, exist_ok=True)

        visited_urls = set()
        crawl_page(archive_url, "web.archive.org", folder, visited_urls)
    else:
        print("No archived snapshot found near the specified date for this URL.")

# Use the function to download the site
url = "http://bogafjell.net"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
download_folder = "bogafjell_net_archive"
year, month, day, hour = 2003, 7, 19, 10

download_site(url, user_agent, download_folder, year, month, day, hour)

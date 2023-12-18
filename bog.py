from waybackpy import WaybackMachineAvailabilityAPI
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import urllib.parse

def download_file(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.basename(urlparse(url).path)
            if not filename:
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

    soup = BeautifulSoup(open(page_content), 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not is_valid_url(href, base_domain):
            href = urljoin(url, href)
        if is_valid_url(href, base_domain):
            crawl_page(href, base_domain, folder, visited)

def crawl_page2(url, base_domain, folder, visited):
    if url in visited:
        return

    print(f"Crawling: {url}")
    visited.add(url)
    page_content = download_file(url, folder)

    if not page_content:
        return

    soup = BeautifulSoup(open(page_content), 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not is_valid_url(href, base_domain):
            href = urljoin(url, href)
        if is_valid_url(href, base_domain):
            crawl_page(href, base_domain, folder, visited)

def download_site(url, user_agent, folder, year, month, day, hour):
    # Initialize the Availability API and find the snapshot near the specified date
    availability_api = WaybackMachineAvailabilityAPI(url, user_agent)
    nearest_snapshot = availability_api.near(year=year, month=month, day=day, hour=hour)

    if nearest_snapshot:
        archive_url = nearest_snapshot.archive_url
        print("Nearest Archived URL:", archive_url)

        # Make directories for downloaded files
        os.makedirs(folder, exist_ok=True)

        # Download the main page
        response = requests.get(archive_url)
        if response.status_code == 200:
            main_page_content = response.text
            main_page_path = os.path.join(folder, "index.html")
            with open(main_page_path, 'w', encoding='utf-8') as file:
                file.write(main_page_content)
            print(f"Main page saved to {main_page_path}")

            # Parse the main page for resources
            soup = BeautifulSoup(main_page_content, 'html.parser')
            for tag in soup.find_all(['img', 'script', 'link'], src=True):
                resource_url = tag['src']
                if not resource_url.startswith('http'):
                    resource_url = urllib.parse.urljoin(archive_url, resource_url)
                download_file(resource_url, folder)

            for link_tag in soup.find_all('link', href=True):
                resource_url = link_tag['href']
                if not resource_url.startswith('http'):
                    resource_url = urllib.parse.urljoin(archive_url, resource_url)
                download_file(resource_url, folder)
        else:
            print(f"Failed to download main page: {archive_url}")
    else:
        print("No archived snapshot found near the specified date for this URL.")

# Use the function to download the site
url = "http://bogafjell.net"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
download_folder = "bogafjell_net_archive"
year, month, day, hour = 2003, 7, 19, 10

download_site(url, user_agent, download_folder, year, month, day, hour)

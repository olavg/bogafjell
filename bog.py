from waybackpy import WaybackMachineAvailabilityAPI
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import urllib

def is_valid_url(url, base_domain):
    return base_domain in url


def download_file(url, base_folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Extract the original path from the Wayback Machine URL
            original_url = url.split('/http:/')[-1].split('/https:/')[-1]
            path = urlparse('http://' + original_url).path
            path_parts = path.split('/')
            filename = path_parts.pop() if path_parts[-1] else 'index.html'
            subfolder_path = os.path.join(base_folder, *path_parts)

            os.makedirs(subfolder_path, exist_ok=True)
            file_path = os.path.join(subfolder_path, filename)


            # First, try to decode using the response encoding
            encoding = response.encoding if response.encoding else 'utf-8'
            try:
                content = response.content.decode(encoding)
            except UnicodeDecodeError:
                # If decoding fails, parse the HTML to find the charset
                soup = BeautifulSoup(response.content, 'html.parser')
                meta = soup.find('meta', attrs={'charset': True})
                if meta:
                    encoding = meta['charset']
                else:
                    meta = soup.find('meta', attrs={'http-equiv': True})
                    if meta and 'content' in meta.attrs:
                        content_type = meta['content']
                        encoding = content_type.split('charset=')[-1]
                content = response.content.decode(encoding, 'ignore')

            with open(file_path, 'w', encoding=encoding) as file:
                file.write(content)
            return file_path, encoding
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None, None

def crawl_page(url, base_domain, folder, visited, encoding='utf-8'):
    if url in visited:
        return

    print(f"Crawling: {url}")
    visited.add(url)
    page_content, page_encoding = download_file(url, folder)

    if not page_content:
        return

    encoding = page_encoding if page_encoding else encoding
    try:
        with open(page_content, 'r', encoding=encoding) as file:
            soup = BeautifulSoup(file, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link['href']
                joined_url = urljoin(url, href)
                if is_valid_url(joined_url, base_domain) and joined_url not in visited:
                    crawl_page(joined_url, base_domain, folder, visited)
    except UnicodeDecodeError as e:
        print(f"Error reading {page_content} with encoding {encoding}: {e}")


def download_site_nearest(url, user_agent, folder, year, month, day, hour):
    availability_api = WaybackMachineAvailabilityAPI(url, user_agent)
    nearest_snapshot = availability_api.near(year=year, month=month, day=day, hour=hour)

    if nearest_snapshot:
        archive_url = nearest_snapshot.archive_url
        print("Nearest Archived URL:", archive_url)

        os.makedirs(folder, exist_ok=True)

        visited_urls = set()
        crawl_page(archive_url, "bogafjell.net", folder, visited_urls)
    else:
        print("No archived snapshot found near the specified date for this URL.")
def download_site(archive_url, folder):
    crawl_page(archive_url, "bogafjell.net", folder, visited_urls)

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

url = "http://bogafjell.net"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
download_folder = "bogafjell_net_archive_v2"
year, month, day, hour = 2003, 7, 19, 10

archive_url = "https://web.archive.org/web/20040128221425/http://www.bogafjell.net/"
download_folder = "bogafjell_net_archive"

download_site(archive_url, download_folder)



#download_site_nearest(url, user_agent, download_folder, year, month, day, hour)

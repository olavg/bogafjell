from waybackpy import WaybackMachineAvailabilityAPI
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse

def is_valid_url(url, base_domain):
    # Extract the original URL from the archived URL
    original_url = url.split('/http:/')[-1].split('/https:/')[-1]
    parsed = urlparse('http://' + original_url)  # Prepend with http:// for proper parsing
    return parsed.netloc.endswith(base_domain)

def download_file(url, base_folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            path = urlparse(url).path
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


def download_site(url, user_agent, folder, year, month, day, hour):
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

url = "http://bogafjell.net"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
download_folder = "bogafjell_net_archive"
year, month, day, hour = 2003, 7, 19, 10

download_site(url, user_agent, download_folder, year, month, day, hour)

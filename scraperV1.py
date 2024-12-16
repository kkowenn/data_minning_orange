import requests
from bs4 import BeautifulSoup
import csv

# Base URL of the website
base_url = "https://www.livinginsider.com/searchword_en/Condo/Rent/1/property-listing-condo-for-rent.html"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}

# Function to get the HTML content of a page
def get_page_content(url):
    response = requests.get(url, headers=headers)
    return response.text

# Function to parse the HTML content
def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup

# Function to extract condo data
def extract_condo_data(soup):
    condos = []
    container_divs = soup.select("div:nth-of-type(3) div.col-md-3.col-sm-4:nth-of-type(n+2)")

    for container in container_divs:
        title = container.select_one("p").text.strip()
        rent_price = container.select_one("div.t-16").text.strip()
        location = container.select_one(".col-xs-12 span").text.strip()
        size = container.select_one("div.col-xs-6:nth-of-type(1)").text.strip()
        click_number = container.select_one("div.istock-view").text.strip()
        floor = container.select_one("div.col-md-5:nth-of-type(2)").text.strip()
        bedroom = container.select_one("div.col-xs-6:nth-of-type(3)").text.strip()
        bathroom = container.select_one("div.col-xs-6:nth-of-type(4)").text.strip()

        condos.append({
            "title": title,
            "rent_price": rent_price,
            "location": location,
            "size": size,
            "click_number": click_number,
            "floor": floor,
            "bedroom": bedroom,
            "bathroom": bathroom
        })

    return condos

# Function to save data to a CSV file
def save_to_csv(data, filename, mode="w"):
    with open(filename, mode, newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        if mode == "w":
            writer.writeheader()
        writer.writerows(data)

# Main script
if __name__ == "__main__":
    current_page = 1
    filename = "condo_rentals.csv"

    try:
        while True:
            print(f"Scraping page {current_page}...")
            page_url = f"{base_url}?page={current_page}"
            html_content = get_page_content(page_url)
            soup = parse_html(html_content)

            condos = extract_condo_data(soup)
            if not condos:
                break

            # Save data to CSV after each page
            save_to_csv(condos, filename, mode="a" if current_page > 1 else "w")
            current_page += 1

    except KeyboardInterrupt:
        print("\nScraping interrupted. Data saved up to the last completed page.")

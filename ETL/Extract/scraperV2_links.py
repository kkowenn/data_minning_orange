import os
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# Define XPaths for different page structures and posts
xpaths = {
    "posts_page1": "/html/body/div[2]/section[2]/div[2]/div[2]/div/div/div/div[3]",
    "posts_page2": "/html/body/div[2]/section[2]/div[2]/div[2]/div/div/div/div",
    "link_variations": [".//a"]
}

# Initialize Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# Function to load processed links from the CSV file
def load_processed_links(filename):
    if not os.path.exists(filename):
        return set()
    try:
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if "Link" not in reader.fieldnames:
                print(f"Warning: Missing 'Link' column in {filename}. Starting fresh.")
                return set()
            return {row["Link"] for row in reader if "Link" in row}
    except Exception as e:
        print(f"Error reading {filename}: {str(e)}. Starting fresh.")
        return set()

# Function to save data incrementally to a CSV file
def save_to_csv(filename, data, fieldnames):
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  # Write header only if the file doesn't exist
        writer.writerows(data)

# Function to scrape a single page (links and click numbers together)
def scrape_page_with_clicks(url, page_number, processed_links):
    print(f"Processing page {page_number}: {url}")
    driver.get(url)
    time.sleep(5)  # Wait for page to load

    # Select the correct root container based on page number
    posts_xpath = xpaths["posts_page1"] if page_number == 1 else xpaths["posts_page2"]

    try:
        root = driver.find_element(By.XPATH, posts_xpath)
        posts = root.find_elements(By.XPATH, "div")  # Collect all div children under root
        print(f"Found {len(posts)} posts on page {page_number}")
    except Exception as e:
        print(f"Error finding posts: {str(e)}")
        posts = []

    combined_data = []
    for index, post in enumerate(posts, start=1):
        try:
            # Extract link
            link = "No Link"
            for link_xpath in xpaths["link_variations"]:
                try:
                    link_elements = post.find_elements(By.XPATH, link_xpath)
                    for link_element in link_elements:
                        href = link_element.get_attribute("href")
                        if href and href.endswith('.html') and href not in processed_links:
                            link = href
                            break
                except Exception:
                    continue

            # Extract click number relative to the post
            click_number = "No Click"
            try:
                click_element = post.find_element(By.XPATH, ".//div[2]/div[2]/div/div[2]")
                click_number = click_element.text.strip() if click_element.text else "No Click"
            except Exception:
                pass

            if link not in processed_links:
                combined_data.append({
                    "Page": page_number,
                    "Index": index,
                    "Link": link,
                    "ClickNumber": click_number
                })
        except Exception as e:
            print(f"Error processing post {index} on Page {page_number}: {str(e)}")
            combined_data.append({
                "Page": page_number,
                "Index": index,
                "Link": "No Link",
                "ClickNumber": "No Click"
            })

    return combined_data

# Main function to control the scraping process
def main():
    base_url = "https://www.livinginsider.com/searchword_en/Condo/Rent/{}/property-listing-condo-for-rent.html"
    total_pages = 500
    output_file = "property_details.csv"

    # Load processed links to avoid duplicates
    processed_links = load_processed_links(output_file)
    print(f"Loaded {len(processed_links)} processed links from {output_file}")

    all_combined_data = []
    fieldnames = ["Page", "Index", "Link", "ClickNumber"]

    for page_number in range(1, total_pages + 1):
        url = base_url.format(page_number)

        # Scrape links and click numbers together
        page_data = scrape_page_with_clicks(url, page_number, processed_links)
        if not page_data:
            print(f"No more data found on page {page_number}. Ending scraping.")
            break

        # Save incrementally
        save_to_csv(output_file, page_data, fieldnames)
        processed_links.update(row["Link"] for row in page_data)
        print(f"Saved {len(page_data)} rows from page {page_number} to {output_file}")

    print(f"Scraping completed. Total data saved to {output_file}.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Data saved up to the last completed page.")
    finally:
        driver.quit()

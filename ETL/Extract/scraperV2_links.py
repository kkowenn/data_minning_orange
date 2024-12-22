# move to main dir
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import csv

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

# Function to scrape a single page (links and click numbers together)
def scrape_page_with_clicks(url, page_number):
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

    # Traverse each post div and extract links and click numbers
    for index, post in enumerate(posts, start=1):
        try:
            # Extract link
            link = "No Link"
            for link_xpath in xpaths["link_variations"]:
                try:
                    link_elements = post.find_elements(By.XPATH, link_xpath)
                    for link_element in link_elements:
                        href = link_element.get_attribute("href")
                        if href and href.endswith('.html'):
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

            # Append extracted data
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
    total_pages = 5
    all_combined_data = []

    for page_number in range(1, total_pages + 1):
        url = base_url.format(page_number)

        # Scrape links and click numbers together
        page_data = scrape_page_with_clicks(url, page_number)
        all_combined_data.extend(page_data)

    # Save combined data to a single CSV file
    with open("condo_data_combined.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Page", "Index", "Link", "ClickNumber"])
        writer.writeheader()
        for row in all_combined_data:
            writer.writerow(row)

    print(f"Saved {len(all_combined_data)} rows to 'condo_data_combined.csv'.")

if __name__ == "__main__":
    try:
        main()
    finally:
        driver.quit()

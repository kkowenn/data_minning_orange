from lxml import html
import requests
import csv
import pandas as pd
import os

# Load links and metadata from condo_data_combined.csv
csv_file_combined = 'condo_data_combined.csv'
combined_data = pd.read_csv(csv_file_combined)

# Filter only rows with valid links
valid_links = combined_data[combined_data["Link"] != "No Link"]

# Filepath for incremental saving
output_file = 'property_details.csv'

# Check if file exists (for resuming)
if os.path.exists(output_file):
    processed_data = pd.read_csv(output_file).to_dict(orient="records")
    processed_links = {row["link"] for row in processed_data}
else:
    processed_data = []
    processed_links = set()

# Function to scrape data for a single property
def scrape_property_details(url):
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the HTML content
        tree = html.fromstring(response.content)

        # Define XPaths for property details
        xpaths = {
            "post_title": [
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[3]/h1',
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[2]/h1'
            ],
            "price": [
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[6]/div[2]/div/span[1]/b',
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[5]/div[2]/div/span[1]/b',
                '/html/body/div[4]/section[2]/div/div[2]/div[1]/div[3]/div[1]/div[5]/div[2]/div/span[1]/b'
            ],
            "price_per_space": [
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[6]/div[3]/div/div/span',
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[7]/div[3]/div/div/span',
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[8]/div[3]/div/div/span',
                '/html/body/div[4]/section[2]/div/div[2]/div[1]/div[3]/div[1]/div[7]/div[3]/div/div/span'
            ],
            "condo_name": [
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[17]/div[1]/div[1]/div[1]/a',
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[16]/div[1]/div[1]/div[1]/a',
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[15]/div[1]/div[1]/div[1]/a'
            ],
            "location": [
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[17]/div[1]/div[1]/div[2]/a',
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[16]/div[1]/div[1]/div[2]/a',
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[15]/div[1]/div[1]/div[2]/a'
            ],
            "space": [
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[5]/div/div[1]/div/div/div[2]/span'
            ],
            "floor": [
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[5]/div/div[3]/div/div/div[2]/span'
            ],
            "bedroom": [
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[5]/div/div[5]/div/div/div[2]/span'
            ],
            "bathroom": [
                '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[5]/div/div[7]/div/div/div[2]/span'
            ]
        }

        # Extract property details with fallback logic
        property_details = {}
        for key, paths in xpaths.items():
            value = "Not Found"
            for xpath in paths:
                try:
                    result = tree.xpath(xpath)
                    if result:
                        value = result[0].text_content().strip()
                        break  # Use the first XPath that works
                except Exception as e:
                    print(f"Error extracting {key} with XPath {xpath}: {e}")
            property_details[key] = value

        # Clean condo_name and location to extract text only
        if property_details["condo_name"] != "Not Found":
            property_details["condo_name"] = property_details["condo_name"].split(">")[-1].strip("<")

        if property_details["location"] != "Not Found":
            property_details["location"] = property_details["location"].split(">")[-1].strip("<")

        # Ensure 'price_per_space' is cleaned properly
        if property_details["price_per_space"] != "Not Found":
            property_details["price_per_space"] = property_details["price_per_space"].replace("(", "").replace(")", "")

        # Clean the 'space' field
        if property_details["space"] != "Not Found":
            property_details["space"] = ''.join(property_details["space"].split())

        return property_details

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# Main function to process all links
def main():
    global processed_data

    try:
        for _, row in valid_links.iterrows():
            url = row["Link"]

            # Skip already processed links
            if url in processed_links:
                print(f"Skipping already processed URL: {url}")
                continue

            print(f"Processing URL: {url}")
            property_details = scrape_property_details(url)

            if property_details:
                # Add metadata from condo_data_combined.csv
                property_details["link"] = url
                property_details["click"] = row["ClickNumber"]
                property_details["Page"] = row["Page"]
                property_details["index"] = row["Index"]

                # Ensure no empty cells
                for key, value in property_details.items():
                    if value == "" or value is None:
                        property_details[key] = "Not Found"

                # Add to processed data
                processed_data.append(property_details)
                processed_links.add(url)

                # Save incrementally
                with open(output_file, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=[
                        "post_title", "condo_name", "location", "price", "price_per_space",
                        "space", "floor", "bedroom", "bathroom",
                        "link", "click", "Page", "index"
                    ])
                    writer.writeheader()
                    writer.writerows(processed_data)

    except KeyboardInterrupt:
        print("\nEarly stopping triggered. Data saved incrementally.")
    except Exception as e:
        print(f"An error occurred: {e}")

    print("Scraping and merging completed. Data saved to property_details.csv.")

if __name__ == "__main__":
    main()

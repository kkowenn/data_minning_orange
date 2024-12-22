import csv
import requests
import pandas as pd
import os
from lxml import html

# Load links and metadata from condo_data_combined.csv
csv_file_combined = 'links.csv'
combined_data = pd.read_csv(csv_file_combined)

# Filter only rows with valid links
valid_links = combined_data[combined_data["Link"] != "No Link"]

# Filepath for incremental saving
output_file = 'property_details.csv'
nearby_file = 'nearby.csv'

# Check if files exist (for resuming)
if os.path.exists(output_file):
    processed_data = pd.read_csv(output_file).to_dict(orient="records")
    processed_links = {row["link"] for row in processed_data}
else:
    processed_data = []
    processed_links = set()

if os.path.exists(nearby_file):
    nearby_data = pd.read_csv(nearby_file).to_dict(orient="records")
    processed_nearby_links = {row["link"] for row in nearby_data}
else:
    nearby_data = []
    processed_nearby_links = set()

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

# Function to scrape nearby places for a property
def scrape_nearby_places(url):
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the HTML content
        tree = html.fromstring(response.content)

        # Define XPaths for nearby places
        nearby_xpath_names = [
            '/html/body/div[4]/section[2]/div/div[2]/div[1]/div[3]/div[2]/div[16]/div/ul/li[1]/a/span/text()',
            '/html/body/div[4]/section[2]/div/div[2]/div[1]/div[3]/div[2]/div[16]/div/ul/li[2]/a/span/text()'
        ]
        nearby_xpath_distances = [
            '/html/body/div[4]/section[2]/div/div[2]/div[1]/div[3]/div[2]/div[16]/div/ul/li[1]/a/p',
            '/html/body/div[4]/section[2]/div/div[2]/div[1]/div[3]/div[2]/div[16]/div/ul/li[2]/a/p'
        ]

        spans_xpath = '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[17]/div/ul/li/a/span'
        paragraphs_xpath = '/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[17]/div/ul/li/a/p'

        nearby_list = []

        # First, try the specified XPaths
        for name_xpath, distance_xpath in zip(nearby_xpath_names, nearby_xpath_distances):
            try:
                name = tree.xpath(name_xpath)
                distance = tree.xpath(distance_xpath)

                if name and distance:
                    name = name[0].strip()
                    distance = distance[0].strip()
                    nearby_list.append({"Name": name, "Distance": distance})
                else:
                    nearby_list.append({"Name": "Not Found", "Distance": "Not Found"})
            except Exception as e:
                print(f"Error extracting nearby element: {e}")
                nearby_list.append({"Name": "Not Found", "Distance": "Not Found"})

        # If the previous XPaths did not find all necessary elements, try the new XPaths
        if not nearby_list or all(item["Name"] == "Not Found" for item in nearby_list):
            spans = tree.xpath(spans_xpath)
            paragraphs = tree.xpath(paragraphs_xpath)

            if spans and paragraphs:
                for span, paragraph in zip(spans, paragraphs):
                    name = span.text_content().strip() if span is not None else "Not Found"
                    distance = paragraph.text_content().strip() if paragraph is not None else "Not Found"
                    nearby_list.append({"Name": name, "Distance": distance})

            if not spans or not paragraphs:
                nearby_list.append({"Name": "Not Found", "Distance": "Not Found"})

        return nearby_list
    except Exception as e:
        print(f"Error scraping nearby places from {url}: {e}")
        return [{"Name": "Not Found", "Distance": "Not Found"}]

# Main function to process all links
def main():
    global processed_data, nearby_data

    # Calculate and print remaining URLs for property details
    remaining_property_details = len(valid_links) - len(processed_links)
    print(f"Remaining property details to process: {remaining_property_details}")

    # Calculate and print remaining URLs for nearby places
    remaining_nearby_places = len(valid_links) - len(processed_nearby_links)
    print(f"Remaining nearby places to process: {remaining_nearby_places}")

    try:
        for _, row in valid_links.iterrows():
            url = row["Link"]

            # Skip already processed links for property details
            if url in processed_links:
                print(f"Skipping already processed property details URL: {url}")
                continue

            print(f"Processing property details URL: {url}")
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

                # Update and print the remaining count after processing each link
                remaining_property_details -= 1
                print(f"Remaining property details to process: {remaining_property_details}")

                # Save incrementally
                with open(output_file, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=[
                        "post_title", "condo_name", "location", "price", "price_per_space",
                        "space", "floor", "bedroom", "bathroom",
                        "link", "click", "Page", "index"
                    ])
                    writer.writeheader()
                    writer.writerows(processed_data)

                # Scrape and save nearby places incrementally
                if url not in processed_nearby_links:
                    print(f"Processing nearby places for URL: {url}")
                    nearby_places = scrape_nearby_places(url)

                    for place in nearby_places:
                        nearby_data.append({
                            "Condo_name": property_details["condo_name"],
                            "NearBy": place["Name"],
                            "Distance": place["Distance"],
                            "link": url
                        })

                    # Update and print the remaining count for nearby places
                    remaining_nearby_places -= 1
                    print(f"Remaining nearby places to process: {remaining_nearby_places}")

                    # Save incrementally to nearby.csv
                    with open(nearby_file, mode='w', newline='', encoding='utf-8') as file:
                        writer = csv.DictWriter(file, fieldnames=["Condo_name", "NearBy", "Distance", "link"])
                        writer.writeheader()
                        writer.writerows(nearby_data)

                    processed_nearby_links.add(url)

    except KeyboardInterrupt:
        print("\nEarly stopping triggered. Data saved incrementally for both property details and nearby places.")
    except Exception as e:
        print(f"An error occurred: {e}")

    print("Scraping and merging completed. Data saved to property_details.csv and nearby.csv.")

if __name__ == "__main__":
    main()

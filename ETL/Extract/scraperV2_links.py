# PostLinkClick.py (get the links) -> get the detail csv file and nearby cvs file

from lxml import html
import requests
import csv
import pandas as pd
import time

# File paths
input_file = "condo_click_numbers.csv"
output_details_file = "property_details.csv"
output_nearby_file = "nearby.csv"

# Load links from the input file
data = pd.read_csv(input_file)

# Filter valid links (where Link column is not "No Link")
valid_links = data[data["Link"] != "No Link"]["Link"]

# Function to extract details from a single property page
def extract_details(link):
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(link)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the HTML content
        tree = html.fromstring(response.content)

        # Extract data using XPaths
        condo_name = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[15]/div[1]/div[1]/div[1]/a')
        price = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[6]/div[2]/div/span[1]')
        post_title = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[3]/h1')
        price_per_space = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[1]/div[8]/div[3]/div/div/span')
        space = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[5]/div/div[1]/div/div/div[2]/span')
        floor = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[5]/div/div[3]/div/div/div[2]/span')
        bedroom = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[5]/div/div[5]/div/div/div[2]/span')
        bathroom = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[5]/div/div[7]/div/div/div[2]/span')

        # Extract condo name
        condo_name_text = condo_name[0].text_content().strip() if condo_name else "Not Found"

        # Prepare property details
        property_data = {
            "post_title": post_title[0].text_content().strip() if post_title else "Not Found",
            "condo_name": condo_name_text,
            "price": price[0].text_content().strip() if price else "Not Found",
            "pricePerSpace": price_per_space[0].text_content().strip() if price_per_space else "Not Found",
            "space": space[0].text_content().strip() if space else "Not Found",
            "floor": floor[0].text_content().strip() if floor else "Not Found",
            "bedroom": bedroom[0].text_content().strip() if bedroom else "Not Found",
            "bathroom": bathroom[0].text_content().strip() if bathroom else "Not Found",
            "link": link,
        }

        # Extract nearby locations
        spans = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[17]/div/ul/li/a/span')
        paragraphs = tree.xpath('/html/body/div[4]/section[2]/div/div/div[1]/div[3]/div[2]/div[17]/div/ul/li/a/p')

        nearby_data = [
            {
                "Condo_name": condo_name_text,
                "NearBy": span.text_content().strip(),
                "distance": paragraph.text_content().strip(),
                "link": link,
            }
            for span, paragraph in zip(spans, paragraphs)
        ]

        return property_data, nearby_data

    except Exception as e:
        print(f"Error extracting details for {link}: {e}")
        return None, None


# Main function to process all links and save the data
def main():
    all_property_details = []
    all_nearby_details = []

    for link in valid_links:
        print(f"Processing link: {link}")
        property_details, nearby_details = extract_details(link)

        if property_details:
            all_property_details.append(property_details)
        if nearby_details:
            all_nearby_details.extend(nearby_details)

        # Add delay to avoid overwhelming the server
        time.sleep(1)

    # Save property details to CSV
    with open(output_details_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["post_title", "condo_name", "price", "pricePerSpace", "space", "floor", "bedroom", "bathroom", "link"])
        writer.writeheader()
        writer.writerows(all_property_details)

    print(f"Property details saved to {output_details_file}")

    # Save nearby locations to CSV
    with open(output_nearby_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Condo_name", "NearBy", "distance", "link"])
        writer.writeheader()
        writer.writerows(all_nearby_details)

    print(f"Nearby locations saved to {output_nearby_file}")


if __name__ == "__main__":
    main()

from playwright.sync_api import sync_playwright
import csv
import csv
import json
import validators
import time

def scrape_canvas_data(page, selector):
    print("Finding all canvas elements on the page...")
    canvas_elements = page.query_selector_all(selector)
    if not canvas_elements:
        print("No canvas elements found.")
        return []
    canvas_data_list = []
    for i, canvas in enumerate(canvas_elements, start=1):
        canvas_data = canvas.get_attribute('data-chart-stats')
        if canvas_data:
            canvas_data_list.append({"canvas_index": i, "data": canvas_data})
    return canvas_data_list

def extract_list_data(page, css_selector):
    print(f"Extracting list data for selector: {css_selector}")
    try:
        elements = page.query_selector_all(css_selector)
        if elements:
            data = []
            for i, element in enumerate(elements, start=1):
                text = element.text_content().strip()
                # Check for nested span elements and append their text content if they exist
                spans = element.query_selector_all('span')
                if spans:
                    for span in spans:
                        text += ' ' + span.text_content().strip()
                data.append(f"{text}")
            return data
        else:
            print(f"No elements found for selector: {css_selector}")
            return []
    except Exception as e:
        print(f"Error extracting list data for selector '{css_selector}': {e}")
        return []

# Extracting span data with the corrected XPath selectors
def extract_xpath_span_data(page, xpath_selector):
    print(f"Extracting span data for selector: {xpath_selector}")
    try:
        locator = page.locator(f"xpath={xpath_selector}")
        elements_count = locator.count()

        if elements_count > 0:
            return [locator.nth(i).text_content().strip() for i in range(elements_count)]
        else:
            print(f"No elements found for selector: {xpath_selector}")
            return []
    except Exception as e:
        print(f"Error extracting span data for selector '{xpath_selector}': {e}")
        return []

# Extracting span data with CSS selectors
def extract_css_span_data(page, css_selector):
    print(f"Extracting span data for selector: {css_selector}")
    try:
        elements = page.query_selector_all(css_selector)
        if elements:
            return [element.text_content().strip() for element in elements]
        else:
            print(f"No elements found for selector: {css_selector}")
            return []
    except Exception as e:
        print(f"Error extracting span data for selector '{css_selector}': {e}")
        return []

def extract_text_data(page, selector):
    print(f"Extracting text data for selector: {selector}")
    try:
        element = page.query_selector(selector)
        if element:
            return element.text_content().strip()
        else:
            print(f"No element found for selector: {selector}")
            return ""
    except Exception as e:
        print(f"Error extracting text data for selector '{selector}': {e}")
        return ""

def parse_canvas_data(canvas_data):
    parsed_data = []
    for canvas in canvas_data:
        canvas_index = canvas.get("canvas_index")
        data_string = canvas.get("data")
        try:
            data = json.loads(data_string)
            for entry in data:
                currency_format = entry.get("currencyStringFormat", "")
                for record in entry.get("data", []):
                    parsed_data.append({
                        "canvas_index": canvas_index,
                        "currencyStringFormat": currency_format,
                        "date": record.get("date", ""),
                        "value": record.get("value", "")
                    })
        except json.JSONDecodeError as e:
            print(f"Error parsing canvas data: {e}")
    return parsed_data

def save_to_csv(data, filename, fieldnames, link):
    if data:
        print(f"Appending data to {filename}...")
        # Add the `link` field to the fieldnames list if not already present
        if "link" not in fieldnames:
            fieldnames.append("link")

        try:
            # Open the file in append mode
            with open(filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                # Write the header only if the file is empty
                if file.tell() == 0:
                    writer.writeheader()

                # Add the link to each record and write the data
                for record in data:
                    record["link"] = link  # Include the link in each record
                    writer.writerow(record)

            print(f"Data appended to {filename} successfully.")
        except Exception as e:
            print(f"Error appending data to {filename}: {e}")
    else:
        print("No data to append.")


def save_facility_data_to_csv(data, filename):
    if data:
        print(f"Appending facility data to {filename}...")
        fieldnames = set()
        for entry in data:
            fieldnames.update(entry.keys())
        fieldnames = sorted(fieldnames)

        try:
            with open(filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                if file.tell() == 0:  # If the file is empty, write the header
                    writer.writeheader()
                writer.writerows(data)
            print(f"Facility data appended to {filename} successfully.")
        except Exception as e:
            print(f"Error appending facility data to {filename}: {e}")
    else:
        print("No facility data to append.")


def read_urls_from_csv(csv_filename):
    urls = []
    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    urls.append(row[0])  # Assuming the URL is in the first column
                    print(f"Read URL: {row[0]}")  # Add this line for debugging
    except Exception as e:
        print(f"Error reading URLs from CSV file: {e}")
    return urls

def save_dataset(canvas_data, facility_data, link):
    historical_data_file = "historical_data.csv"
    facility_data_file = "Facility.csv"

    # Historical Data: Canvas Data
    historical_fieldnames = ["canvas_index", "currencyStringFormat", "date", "value", "link"]

    if canvas_data:
        print(f"Saving canvas data to {historical_data_file}...")
        try:
            with open(historical_data_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=historical_fieldnames)
                if file.tell() == 0:
                    writer.writeheader()
                for record in canvas_data:
                    record["link"] = link
                    writer.writerow(record)
            print(f"Canvas data saved to {historical_data_file} successfully.")
        except Exception as e:
            print(f"Error saving canvas data to {historical_data_file}: {e}")
    else:
        print("No canvas data to save.")

    # Facility Data: Handle unexpected fields dynamically
    base_fieldnames = [
        "condo_name", "building", "floor", "unit", "for_rent_price", "for_rent_price_per_space",
        "for_rent_evolution", "for_sale_price", "for_sale_price_per_space", "for_sale_evolution",
        "location", "Features 1", "Features 2", "Features 3", "Features 4",
        "Management 1", "Management 2", "Parking and Lifts 1", "Parking and Lifts 2", "link"
    ]

    if facility_data:
        print(f"Saving facility data to {facility_data_file}...")

        # Dynamically handle additional fields in facility_data
        current_fieldnames = base_fieldnames.copy()
        extra_fields = [field for field in facility_data.keys() if field not in current_fieldnames]
        current_fieldnames.extend(extra_fields)

        try:
            with open(facility_data_file, mode='a+', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=current_fieldnames)
                # Write the header only if the file is empty
                if file.tell() == 0:
                    writer.writeheader()
                facility_data["link"] = link  # Add the link to the facility data
                writer.writerow(facility_data)
            print(f"Facility data saved to {facility_data_file} successfully.")
        except Exception as e:
            print(f"Error saving facility data to {facility_data_file}: {e}")
    else:
        print("No facility data to save.")


def is_url_processed(url, facility_csv):
    """Check if the URL has already been processed in Facility.csv."""
    try:
        with open(facility_csv, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("link") == url:
                    return True
    except FileNotFoundError:
        print(f"{facility_csv} not found. It will be created.")
    except Exception as e:
        print(f"Error checking URL in {facility_csv}: {e}")
    return False

def process_url(url, url_index, total_urls):
    facility_csv = "Facility.csv"

    # Skip processing if the URL is already in Facility.csv
    if is_url_processed(url, facility_csv):
        print(f"Skipping already processed URL: {url}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"Processing {url_index + 1}/{total_urls}: Navigating to URL: {url}")
        page.goto(url)

        # Handle CAPTCHA manually with user input
        print("Solve the CAPTCHA manually if it appears, then press ENTER to continue.")
        input("Press ENTER after solving the CAPTCHA...")

        try:
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Page load state timeout or error: {e}")

        canvas_data = []
        facility_data = {}

        # Extract Canvas Data
        canvas_selector = "canvas"
        try:
            canvas_data_raw = scrape_canvas_data(page, canvas_selector)
            canvas_data = parse_canvas_data(canvas_data_raw)
        except Exception as e:
            print(f"Error extracting canvas data: {e}")

        # Extract List Data
        list_selectors = [
            ("section:nth-of-type(4) > div:nth-of-type(1) > ul > li", "Features"),
            ("section:nth-of-type(4) > div:nth-of-type(2) > ul > li", "Parking and Lifts"),
            ("section:nth-of-type(4) > div:nth-of-type(3) > ul > li", "Management")
        ]
        for selector, section in list_selectors:
            try:
                list_data = extract_list_data(page, selector)
                for i, item in enumerate(list_data, start=1):
                    facility_data[f"{section} {i}"] = item
            except Exception as e:
                print(f"Error processing list data for selector '{selector}': {e}")

        # Extract Span Data with XPath
        xpath_selectors = [
            ("/html/body/main/div[3]/div[3]/div[2]/div[1]/span[2]", "for_rent_price"),
            ("/html/body/main/div[3]/div[3]/div[2]/div[1]/span[3]", "for_rent_price_per_space"),
            ("/html/body/main/div[3]/div[3]/div[2]/div[1]/span[4]", "for_rent_evolution")
        ]
        for xpath_selector, section in xpath_selectors:
            try:
                span_data = extract_xpath_span_data(page, xpath_selector)
                if span_data:
                    facility_data[section] = span_data[0]
            except Exception as e:
                print(f"Error processing data for selector '{xpath_selector}': {e}")

        # Extract Span Data with CSS
        css_selectors = [
            ("div.main-header > section.characteristics > div.completed > span.data", "off_plan"),
            ("div.main-header > section.characteristics > div.floor > span.data", "floor"),
            ("div.main-header > section.characteristics > div.buildings > span.data", "building"),
            ("div.main-header > section.characteristics > div.units > span.data", "unit"),
            ("div.main-header > section.title > h1", "condo_name"),
            ("div.main-header > section.title > span.location", "location"),
            (".market-stats__by-operation__summary__price.median", "for_sale_price"),
            (".market-stats__by-operation__summary__price.per-area", "for_sale_price_per_space"),
            (".market-stats__by-operation__summary__progress", "for_sale_evolution")
        ]
        for css_selector, section in css_selectors:
            try:
                span_data = extract_css_span_data(page, css_selector)
                if span_data:
                    facility_data[section] = span_data[0]
            except Exception as e:
                print(f"Error processing data for selector '{css_selector}': {e}")

        # Save the dataset with the current URL
        save_dataset(canvas_data, facility_data, url)

        browser.close()


def main():
    csv_filename = "link2.csv"
    urls = read_urls_from_csv(csv_filename)
    total_urls = len(urls)

    for url_index, url in enumerate(urls):
        if validators.url(url):
            process_url(url, url_index, total_urls)
        else:
            print(f"Skipping invalid URL: {url}")

if __name__ == "__main__":
    main()

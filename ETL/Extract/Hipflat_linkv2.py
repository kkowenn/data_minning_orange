from playwright.sync_api import sync_playwright
import csv
import signal
import sys

def extract_links(page, base_xpath):
    links = []
    try:
        link_elements = page.locator(f"xpath={base_xpath}")
        elements_count = link_elements.count()

        for i in range(elements_count):
            link = link_elements.nth(i).get_attribute("href")
            if link:
                links.append(link)
    except Exception as e:
        print(f"Error extracting links: {e}")
    return links

def save_links_to_csv(links, filename, mode="w"):
    if links:
        print(f"Saving links to {filename}...")
        with open(filename, mode=mode, newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if mode == "w":
                writer.writerow(["Link"])
            for link in links:
                writer.writerow([link])
        print(f"Links saved to {filename} successfully.")
    else:
        print("No links to save.")

def main():
    base_url = "https://www.hipflat.co.th/en/thailand-projects/condo/bangkok-bm?page="
    base_xpath = "/html/body/main/div[3]/div//a"
    csv_filename = "links.csv"

    links = []

    def handle_interrupt(sig, frame):
        print("\nInterrupt received, saving accumulated data...")
        save_links_to_csv(links, csv_filename, mode="a")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            for i in range(1, 51):  # Loop from page 1 to 50
                url = base_url + str(i)
                print(f"Navigating to URL: {url}")
                page.goto(url)

                print("Solve the CAPTCHA manually if it appears, then press ENTER to continue.")
                input("Press ENTER after solving CAPTCHA...")

                try:
                    page.wait_for_load_state("networkidle")
                except Exception as e:
                    print(f"Page load state timeout or error: {e}")

                try:
                    page_links = extract_links(page, base_xpath)
                    print(f"Extracted links from page {i}: {page_links}")
                    links.extend(page_links)

                    # Save links incrementally after each page
                    save_links_to_csv(page_links, csv_filename, mode="a")
                except Exception as e:
                    print(f"Error extracting links on page {i}: {e}")

            browser.close()
    except Exception as e:
        print(f"An error occurred: {e}")

    # Save any remaining links after loop ends
    save_links_to_csv(links, csv_filename, mode="a")

if __name__ == "__main__":
    main()

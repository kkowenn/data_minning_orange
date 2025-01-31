from playwright.sync_api import sync_playwright
import csv

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

def save_links_to_csv(links, filename):
    if links:
        print(f"Saving links to {filename}...")
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Link"])
            for link in links:
                writer.writerow([link])
        print(f"Links saved to {filename} successfully.")
    else:
        print("No links to save.")

def main():
    url = "https://www.hipflat.co.th/en/thailand-projects/condo/bangkok-bm"
    base_xpath = "/html/body/main/div[3]/div//a"
    csv_filename = "link.csv"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navigating to URL: {url}")
        page.goto(url)

        print("Solve the CAPTCHA manually if it appears, then press ENTER to continue.")
        input("Press ENTER after solving CAPTCHA...")

        try:
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Page load state timeout or error: {e}")

        try:
            links = extract_links(page, base_xpath)
            print(f"Extracted links: {links}")
        except Exception as e:
            print(f"Error extracting links: {e}")

        browser.close()

    save_links_to_csv(links, csv_filename)

if __name__ == "__main__":
    main()

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def search_amazon(driver, query):
    driver.get(f"https://www.amazon.in/s?k={query.replace(' ', '+')}")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
        )
    )


def get_top_10_products(driver, limit=3):
    products = driver.find_elements(
        By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
    links = []

    for p in products:
        if len(links) == limit:
            break
        try:
            link = p.find_element(
                By.CSS_SELECTOR, "a.a-link-normal.s-no-outline"
            ).get_attribute("href")
            if link and "/dp/" in link:
                links.append(link)
        except:
            continue

    return links


def get_price(driver):
    prices = driver.find_elements(By.CSS_SELECTOR, "span.a-price-whole")
    for p in prices:
        text = p.text.replace(",", "").strip()
        if text.isdigit():
            return int(text)
    return None


def get_rating(driver):
    try:
        return driver.find_element(
            By.CSS_SELECTOR, "span[data-hook='rating-out-of-text']"
        ).text
    except:
        return None


def get_reviews(driver, max_reviews=5):
    reviews = []
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight * 0.75)"
    )
    time.sleep(1)

    elements = driver.find_elements(
        By.CSS_SELECTOR, "span[data-hook='review-body']"
    )

    for e in elements:
        if len(reviews) == max_reviews:
            break
        text = e.text.strip()
        if len(text) > 30:
            reviews.append(text)

    return reviews


def get_title(driver):
    try:
        return driver.find_element(By.ID, "productTitle").text.strip()
    except:
        return None


def get_image_url(driver):
    try:
        img = driver.find_element(By.ID, "landingImage")
        return img.get_attribute("data-old-hires") or img.get_attribute("src")
    except:
        return None


def scrape_product(driver, url):
    driver.get(url)
    time.sleep(1)

    return {
        "title": get_title(driver),
        "image": get_image_url(driver),
        "price": get_price(driver),
        "rating": get_rating(driver),
        "reviews": get_reviews(driver),
        "url": url,
    }


# ================== NEW (ONLY ADDITION) ==================
def scrape_amazon_products(query, limit=3):
    driver = get_driver()
    try:
        search_amazon(driver, query)
        links = get_top_10_products(driver, limit)

        products = []
        for link in links:
            products.append(scrape_product(driver, link))

        return products
    finally:
        driver.quit()

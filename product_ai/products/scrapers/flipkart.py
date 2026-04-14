import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def log(msg):
    print(f"[DEBUG] {msg}")


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def close_login_popup(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='✕']"))
        ).click()
        log("Login popup closed")
    except:
        log("No login popup found")


def search_flipkart(driver, query):
    log("Opening Flipkart")
    driver.get("https://www.flipkart.com")

    close_login_popup(driver)

    log("Searching product")
    search = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "q"))
    )
    search.send_keys(query)
    search.submit()

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/p/')]"))
    )
    log("Search results loaded")


def get_top_products(driver, limit=3):
    anchors = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
    log(f"Total /p/ links found: {len(anchors)}")

    links = []
    for a in anchors:
        if len(links) == limit:
            break
        href = a.get_attribute("href")
        if href and href.startswith("https://www.flipkart.com"):
            links.append(href)

    log(f"Collected {len(links)} product links")
    return links


def wait_for_product_page(driver):
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(1)


def get_title(driver):
    try:
        title = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.LMizgS"))
        ).text.strip()
        log(f"Title: {title}")
        return title
    except:
        log("Title not found")
        return None


def get_price(driver):
    try:
        price_text = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.hZ3P6w"))
        ).text
        price = int(price_text.replace("₹", "").replace(",", ""))
        log(f"Price: {price}")
        return price
    except:
        log("Price not found")
        return None


def get_rating(driver):
    try:
        rating = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.MKiFS6"))
        ).text.strip()
        log(f"Rating: {rating}")
        return rating
    except:
        log("Rating not found")
        return None


def get_image(driver):
    try:
        log("Waiting for product image via XPath")
        img = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//*[@id='container']/div/div[3]/div[1]/div[1]/div[1]/div/div[1]/div[2]/div/div[2]/img"
            ))
        )
        src = img.get_attribute("src")
        log("Image URL found")
        return src
    except Exception as e:
        log(f"Image not found: {e}")
        return None


def get_reviews(driver, max_reviews=5):
    reviews = []
    try:
        review_titles = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "p.qW2QI1")
            )
        )

        log(f"Review titles found: {len(review_titles)}")

        for r in review_titles:
            if len(reviews) == max_reviews:
                break
            text = r.text.strip()
            if text:
                reviews.append(text)

        log(f"Collected {len(reviews)} review titles")
    except:
        log("Review titles not found")

    return reviews


def scrape_product(driver, url):
    log(f"Opening product page: {url}")
    driver.get(url)

    # extra wait for JS hydration
    time.sleep(3)

    # retry once if title not loaded
    title = get_title(driver)
    if title is None:
        log("Retrying product page load")
        driver.refresh()
        time.sleep(3)

    return {
        "title": get_title(driver),
        "image": get_image(driver),
        "price": get_price(driver),
        "rating": get_rating(driver),
        "reviews": get_reviews(driver),
        "url": url
    }



# ================== NEW (ONLY ADDITION) ==================
def scrape_flipkart_products(query, limit=3):
    driver = get_driver()
    try:
        search_flipkart(driver, query)
        links = get_top_products(driver, limit)

        products = []
        for link in links:
            products.append(scrape_product(driver, link))

        return products
    finally:
        driver.quit()

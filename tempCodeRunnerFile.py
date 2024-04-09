import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import mysql.connector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def extract_article_info(url):
    # Initialize Selenium webdriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)

    # Explicitly wait for dynamically loaded elements (e.g., views, comments)
    wait = WebDriverWait(driver, 10)  # Adjust time as needed

    articles = []
    # Wait for the first instance of dynamically loaded content before proceeding
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".content_item_meta_viewings .tn-text-preloader-dark")))

    # Now, it's safe to parse the page source with Beautiful Soup
    soup = BeautifulSoup(driver.page_source, "html.parser")

    for article_element in soup.find_all("div", class_="main-news_top_item"):
        title_element = article_element.find("span", class_="main-news_top_item_title")
        image_element = article_element.find("img", class_="main-news_top_item_img")
        time_element = article_element.find("time")

        # Since views and comments are dynamically loaded, they should be accessible now
        views_element = article_element.find("span", class_="content_item_meta_viewings")
        comments_element = article_element.find("span", class_="content_item_meta_comments")

        article_info = {
            "title": title_element.text.strip() if title_element else None,
            "image": image_element["src"] if image_element else None,
            "time": time_element.text.strip() if time_element else None,
            "views": views_element.text.strip() if views_element else None,
            "comments": comments_element.text.strip() if comments_element else None,
        }
        articles.append(article_info)

    driver.quit()  # Ensure the browser is closed after scraping
    return articles


import mysql.connector

def save_articles_to_db(articles):
    # Replace with your MySQL connection details
    config = {
        'user': 'root',
        'password': '12345',
        'host': 'localhost',
        'database': 'tengri'
    }

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # Create table if it doesn't exist (MySQL syntax)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INT AUTO_INCREMENT PRIMARY KEY,  # Add an auto-incrementing primary key
            title TEXT,
            image TEXT,
            time TEXT
        )
    """)

    for article in articles:
        cursor.execute("""
            INSERT INTO articles (title, image, time)
            VALUES (%s, %s, %s)
        """, (article["title"], article["image"], article["time"]))


    conn.commit()  # Save changes
    conn.close()

# Example usage
url = "https://tengrinews.kz/"
articles = extract_article_info(url)
save_articles_to_db(articles)

for article in articles:
    print(f"Title: {article['title']}")
    print(f"Image: {article['image']}")
    print(f"Time: {article['time']}")
    print(f"Views: {article['views']}")
    print(f"Comments: {article['comments']}")
    print("-" * 20)
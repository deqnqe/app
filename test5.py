import requests
from bs4 import BeautifulSoup
#import psycopg2
from urllib.parse import urlparse
from datetime import datetime, timedelta
import mysql.connector

months = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12
}

def parse_publication_date(date_str):
    if "Сегодня" in date_str:
        time_part = date_str.split()[1] if len(date_str.split()) > 1 else "00:00"
        publication_date = datetime.now().replace(hour=int(time_part.split(":")[0]), minute=int(time_part.split(":")[1]), second=0, microsecond=0)
    elif "Вчера" in date_str:
        time_part = date_str.split()[1] if len(date_str.split()) > 1 else "00:00"
        yesterday = datetime.now() - timedelta(days=1)
        publication_date = yesterday.replace(hour=int(time_part.split(":")[0]), minute=int(time_part.split(":")[1]), second=0, microsecond=0)
    else:
        date_parts = date_str.split()
        month_number = months.get(date_parts[1].lower(), 1) 
        date_string = f"{date_parts[0]} {month_number} {date_parts[2]} {date_parts[3]}"
        publication_date = datetime.strptime(date_string, "%d %m %Y %H:%M")
    
    return publication_date.isoformat()

def extract_tag_from_url(url):
    if isinstance(url, bytes):
        url = url.decode('utf-8') 

    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')[0]
    if domain_parts == 'tengrinews':
        tag = parsed_url.path.strip("/").split("/")[0]
    else:
        tag = domain_parts
    return tag

def extract_article_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []


    for article_element in soup.find_all("div", class_="main-news_top_item"):
        title_element = article_element.find("span", class_="main-news_top_item_title")
        image_element = article_element.find("img", class_="main-news_top_item_img")
        time_element = article_element.find("time")
        views_element = article_element.find("span", class_="content_item_meta_viewings")
        comments_element = article_element.find("span", class_="content_item_meta_comments")
        link_element = article_element.find("a", href=True)

        article_url = link_element['href'] if link_element else None
        if article_url and not article_url.startswith('http'):
            article_url = url.rstrip('/') + '/' + article_url.lstrip('/')
        
        content = None
        if article_url:
            article_response = requests.get(article_url)
            article_soup = BeautifulSoup(article_response.content, "html.parser")
            content_element = article_soup.find("div", class_="content_main_text")
            if content_element:
                content = str(content_element) 
            else:
                content_element = article_soup.find("div", class_="post-content")
                content = str(content_element) if content_element else None
            

        if article_url:
            article_response = requests.get(article_url)
            article_soup = BeautifulSoup(article_response.content, "html.parser")
            time_element = article_soup.find("div", class_="date-time")
            if time_element:
                timestamp = parse_publication_date(time_element.text.strip())
            if time_element is None:
                time_element = article_soup.find("span", class_="date")
                timestamp = parse_publication_date(time_element.text.strip())
            if time_element is None:
                timestamp = None
         
        tag = "tengrinews"  
        logo_element_link = article_soup.find("a", class_="menu_logo")
        if logo_element_link:  
            logo_element = logo_element_link.find("img")
            if logo_element:
                logo_src = logo_element.get('src', '')
                tag_parts = logo_src.split('/')
                if "tengriguide" in tag_parts:
                    tag = "tengriguide"
                elif "edu" in tag_parts:
                    tag = "tengriedu"
                elif "auto" in tag_parts:
                    tag = "tengriauto"
                elif "tengri_sport" in tag_parts:
                    tag = "tengrisport"
        else:
            travel_logo = article_soup.find("img", class_="tn-travel-logo")
            if travel_logo:
                tag = "tengritravel"
            else:
                tag = "tengrinews"

        article_info = {
            "title": title_element.text.strip() if title_element else "",
            "image": image_element["src"] if image_element else "",
            "timestamp": timestamp,
            "views": views_element.text.strip() if views_element else "",
            "comments": comments_element.text.strip() if comments_element else "",
            "url": article_url,
            "content": content,
            "tags": tag
        }

        articles.append(article_info)

    return articles

def save_articles_to_db(articles):
    config = {
        'user': 'root',
        'password': '12345',
        'host': 'localhost',
        'database': 'news',
        'raise_on_warnings': True
    }

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT,
            image TEXT,
            timestamp TEXT,
            views TEXT,
            comments TEXT,
            url TEXT,
            content TEXT,
            tags TEXT
        )
    """)

    existing_urls_query = "SELECT url FROM articles"
    cursor.execute(existing_urls_query)
    existing_urls = set(row[0] for row in cursor.fetchall())

    for article in articles:
        if article["url"] in existing_urls:
            print(f"Article already exists: {article['url']}")
            continue  

        cursor.execute("""
            INSERT INTO articles (title, image, timestamp, views, comments, url, content, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (article["title"], article["image"], article["timestamp"], article["views"], article["comments"], article["url"], article["content"], article["tags"]))

        existing_urls_query = "SELECT url FROM articles"
        cursor.execute(existing_urls_query)
        existing_urls = set(row[0] for row in cursor.fetchall())
    conn.commit()
    conn.close()

url = "https://tengrinews.kz/"
articles = extract_article_info(url)
save_articles_to_db(articles)

for article in articles:
    print(f"Title: {article['title']}")
    print(f"Image: {article['image']}")
    print(f"Time: {article['timestamp']}")
    print(f"Views: {article['views']}")
    print(f"Comments: {article['comments']}")
    print(f"URL: {article['url']}")
    print(f"Tags: {article['tags']}")
    if article['content'] is not None:
        print(f"Content: {article['content'][:100]}...")  
    else:
        print("Content: None")
    print("-" * 20)

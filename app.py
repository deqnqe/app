from flask import Flask, render_template, request
import mysql.connector
from datetime import datetime
app = Flask(__name__)
url = "https://tengrinews.kz/"


def get_articles_from_db(tags):
    config = {
        'user': 'root',
        'password': '12345',
        'host': 'localhost',
        'database': 'news',
        'raise_on_warnings': True
    }
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM articles WHERE tags LIKE %s ORDER BY timestamp DESC LIMIT 20"
    cursor.execute(query, ("%{}%".format(tags),))
    articles = cursor.fetchall()
    filtered_articles = [article for article in articles if article['content'] and article['image'] and article['title'] and article['timestamp'] and article['url'] and article['content'] and article['tags']]
    cursor.close()
    conn.close()

    return filtered_articles

@app.route('/', defaults={'tags': 'tengrinews'})
@app.route('/<tags>')
def index(tags):
    if tags == 'tengrilife':
        tags = 'tengrinews'

    articles = get_articles_from_db(tags)

    for article in articles:
        timestamp = datetime.fromisoformat(article['timestamp'])
        article['formatted_timestamp'] = timestamp.strftime("%d %B %H:%M")

    return render_template('index.html', articles=articles, current_tag=tags)


@app.route('/article/<int:article_id>')
def article(article_id):
    article = get_article_by_id(article_id)
    if article:
        return render_template('article.html', article=article, is_article_page=True)


def get_article_by_id(article_id):
    config = {
        'user': 'root',
        'password': '12345',
        'host': 'localhost',
        'database': 'news',
        'raise_on_warnings': True
    }
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
    article = cursor.fetchone()
    cursor.close()
    conn.close()
    return article

@app.route('/search')
def search_results():
    query = request.args.get('query', '')
    articles = search_articles_in_db(query)
    
    for article in articles:
        timestamp = datetime.fromisoformat(article['timestamp'])
        article['formatted_timestamp'] = timestamp.strftime("%d %B %H:%M")
    
    return render_template('index.html', articles=articles, current_tag='search')

def search_articles_in_db(query):
    config = {
        'user': 'root',
        'password': '12345',
        'host': 'localhost',
        'database': 'news',
        'raise_on_warnings': True
    }
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    search_query = "SELECT * FROM articles WHERE title LIKE %s OR content LIKE %s ORDER BY timestamp DESC"
    like_query = f"%{query}%"
    cursor.execute(search_query, (like_query, like_query))
    
    articles = cursor.fetchall()
    filtered_articles = [article for article in articles if article['content'] and article['image'] and article['title'] and article['timestamp'] and article['url'] and article['views'] and article['content'] and article['tags']]
    cursor.close()
    conn.close()
    return filtered_articles

if __name__ == '__main__':
    app.run(debug=True)

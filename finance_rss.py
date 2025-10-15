import feedparser
import requests
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom
import json
from bs4 import BeautifulSoup  # Для scraping, если нужно

# Список RSS-фидов для источников (на основе поиска; для Telegram - сгенерированные через TwitRSS или аналог)
RSS_FEEDS = {
    'Interfax Business': 'https://rss.interfax.ru/r/304',  # Бизнес-раздел
    'BCS Valyutnyy Rynok': 'https://bcs-express.ru/feed/',  # Общий фид сайта (если нет категории, используйте scraping)
    'BCS Rossiyiskiy Rynok': 'https://bcs-express.ru/feed/',  # Аналогично
    'RBC Quote': 'https://static.feed.rbc.ru/rbc/logical/footer/news.rss',  # Общий новости RBC (фильтр по тегам в скрипте)
    'RG Ekonomika': 'https://rg.ru/xml/index.xml',  # Общий, включая экономику
    'InvestFuture': 'https://investfuture.ru/feed/',  # Предполагаемый; если нет, используйте RSS.app
    'AlfaCapital TG': 'https://twitrss.me/twitter_user_to_rss/?user=alfacapital',  # Генерация для Telegram через TwitRSS (замените на реальный username)
    'BCS Express TG': 'https://twitrss.me/twitter_user_to_rss/?user=bcs_express',  # Аналогично
    'Kommersant Finance': 'https://www.kommersant.ru/RSS/finance.xml'  # Финансы
}

def fetch_recent_entries(hours=72):
    """Собирает свежие статьи за последние N часов из всех фидов."""
    three_days_ago = datetime.now() - timedelta(hours=hours)
    all_entries = []
    for name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Парсинг даты (feedparser нормализует)
                pub_date = entry.get('published_parsed')
                if pub_date:
                    pub_date = datetime(*pub_date[:6])
                else:
                    pub_date = datetime.now()
                
                if pub_date > three_days_ago:
                    all_entries.append({
                        'title': entry.get('title', 'No title'),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'source': name,
                        'pub_date': pub_date
                    })
        except Exception as e:
            print(f"Ошибка при парсинге {name}: {e}")
            # Fallback: scraping главной страницы (упрощенно)
            try:
                response = requests.get(url.replace('/feed/', '') if 'feed' in url else url)
                soup = BeautifulSoup(response.content, 'html.parser')
                # Пример: найти статьи (адаптируйте под сайт)
                articles = soup.find_all('article')[:5]  # Пример селектора
                for art in articles:
                    title = art.find('h2').text.strip() if art.find('h2') else 'No title'
                    link = art.find('a')['href'] if art.find('a') else ''
                    all_entries.append({
                        'title': title,
                        'link': link,
                        'summary': art.find('p').text.strip() if art.find('p') else '',
                        'source': name,
                        'pub_date': datetime.now()  # Примерная дата
                    })
            except:
                pass  # Игнорируем ошибки scraping для простоты
    
    # Сортировка по дате (новые сначала)
    return sorted(all_entries, key=lambda x: x['pub_date'], reverse=True)

def create_rss(entries, output_file='finance_combined.xml'):
    """Создает RSS-фид из собранных статей."""
    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = 'Combined Finance RSS'
    SubElement(channel, 'link').text = 'https://example.com'  # Ваш сайт
    SubElement(channel, 'description').text = 'Объединенные финансовые новости из источников'
    SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    
    for entry in entries:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = entry['title']
        SubElement(item, 'link').text = entry['link']
        SubElement(item, 'description').text = entry['summary']
        SubElement(item, 'pubDate').text = entry['pub_date'].strftime('%a, %d %b %Y %H:%M:%S %z')
        SubElement(item, 'guid').text = entry['link']
        SubElement(item, 'source').text = entry['source']  # Кастомное поле
    
    xml_str = tostring(rss, encoding='unicode')
    pretty_xml = xml.dom.minidom.parseString(xml_str).toprettyxml(indent='  ')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    print(f'RSS создан: {output_file}')

def save_as_json(entries, output_file='finance_combined.json'):
    """Альтернатива: сохранение в JSON для удобства."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2, default=str)
    print(f'JSON создан: {output_file}')

# Запуск
if __name__ == '__main__':
    entries = fetch_recent_entries(hours=72)
    print(f'Найдено {len(entries)} свежих статей.')
    create_rss(entries)
    save_as_json(entries)
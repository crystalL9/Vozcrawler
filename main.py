import threading
from crawler import VozCrawler

if __name__ == "__main__":
    crawler = VozCrawler()
    url='https://voz.vn/whats-new/posts'
    crawler.get_link(url)
    thread2 = threading.Thread(target=crawler.find_articles_with_classes)
    thread2.start()
    thread2.join()
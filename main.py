import threading
from crawler import VozCrawler

if __name__ == "__main__":
    #url = "https://voz.vn/t/cam-lap-thread-thao-luan-ve-nhan-su-dang-nha-nuoc-chinh-quyen-cac-vu-an-nhay-cam-tin-tuc-lien-quan-nga-ukraine-bau-cu-my-vi-pham-kia.523604/"
    # url='https://voz.vn/p/30448103/reactions'
    # url='https://voz.vn/t/evn-ha-noi-chot-chi-so-cong-to-dien-vao-ngay-cuoi-thang.924035|123|123'
    crawler = VozCrawler()
    url='https://voz.vn/whats-new/posts'
    #url='https://voz.vn/f/gop-y.3/'
    thread1 = threading.Thread(target=crawler.get_link, args=(url,))
    thread2 = threading.Thread(target=crawler.find_articles_with_classes)

    # Start threads
    thread1.start()
    thread1.join()
    # thread2.start()

    # # Wait for both threads to finish
    
    # thread2.join()
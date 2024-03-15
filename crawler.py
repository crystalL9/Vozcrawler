from datetime import datetime
import json
import time
import re
import queue
import threading
import urllib.parse
from Browser import ChromiumBrowser

class VozCrawler :
    link_queue = queue.Queue()
    reactions_queue = queue.Queue()
    json_file_path = 'dev_config.json'
    with open(json_file_path, 'r') as file:
            data = json.load(file)
    proxy_post=data['proxy_post']
    proxy_link=data['proxy_link']
    fake=data['use_cookie']
    reset=data['use_proxy']
    def find_articles_with_classes(self):
        while True:
            if not self.link_queue.empty():
                # for _ in range(4):
                #     self.link_queue.get()
                url=self.link_queue.get()
                link=str(url).split('|')[0]
                comments=str(url).split('|')[1]
                views=str(url).split('|')[2]
                print(f"Crawl all data of all pages from {link}")
                chromium=ChromiumBrowser(fake=self.fake, proxy=self.proxy_post,reset=self.reset)
                chromium.page.goto(link,timeout=600000)
                element = chromium.page.query_selector(".p-title-value")
                title = element.inner_text()
                page_num = 0
                articles = chromium.page.query_selector_all('article.message.message--post.js-post.js-inlineModContainer')
                source_id = articles[0].get_attribute('id')
                next_link=''
                while next_link!=None:
                    if page_num > 0:
                        chromium.close()
                        time.sleep(10)
                        chromium=ChromiumBrowser(fake=self.fake, proxy=self.proxy_post,reset=self.reset)
                        chromium.page.goto(next_link,timeout=600000)
                    try:
                        next_link_elm = chromium.page.query_selector('a.pageNav-jump.pageNav-jump--next')
                        next_link = 'https://voz.vn'+next_link_elm.get_attribute('href')
                    except:
                        next_link = None
                    try:
                        expand_links = chromium.page.query_selector_all(".bbCodeBlock-expandLink.js-expandLink")[0]
                        expand_links.click()
                    except:
                        pass
                    try:
                        spoiler = chromium.page.query_selector_all(".bbCodeSpoiler-button.button")[0]
                        spoiler.click()
                    except:
                        pass
                    articles = chromium.page.query_selector_all('article.message.message--post.js-post.js-inlineModContainer')
                    for article in articles:
                        try:
                            expand_links = article.query_selector_all(".bbCodeBlock-expandLink.js-expandLink")[0]
                            expand_links.click()
                        except:
                            pass
                        try:
                            spoiler = article.query_selector_all(".bbCodeSpoiler-button.button")[0]
                            spoiler.click()
                        except:
                            pass
                        data_crawl={}
                        current_time = datetime.now()
                        timestamp = current_time.timestamp()
                        data_crawl['time_crawl']=int(timestamp)
                        type = article.get_attribute('itemtype')
                        if type==None:
                            type='voz post'
                        elif 'Comment' in type :
                            type='voz comment'
                        
                        data_crawl['type']=type
                        data_crawl['domain']='voz.vn'
                        data_crawl['author'] = article.get_attribute('data-author')
                        id_post=article.get_attribute('id')
                        div_avatar = article.query_selector('div.message-avatar-wrapper')
                        a_element = div_avatar.query_selector('a')
                        link_author= a_element.get_attribute('href')
                        id_user= a_element.get_attribute('data-user-id')
                        data_crawl['id_user'] = id_user
                        data_crawl['author_link']='https://voz.vn'+link_author
                        try:
                            img_element = a_element.query_selector('img')
                            src_avatar = img_element.get_attribute('src')
                        except:
                            src_avatar=''
                        data_crawl['avatar']=src_avatar
                        user_detail_divs = article.query_selector('div.message-userDetails')
                        user_title_element = user_detail_divs.query_selector('.userTitle.message-userTitle')
                        role = user_title_element.inner_text()
                        data_crawl['role']=role
                        if type=='voz post':
                            data_crawl['title']= str(title).split('\xa0')[-1]
                            data_crawl['source_id']=''
                            data_crawl['comments']= int(comments)
                            data_crawl['views'] = int(views)
                        else:
                            data_crawl['source_id']=source_id
                            data_crawl['title']= ''
                            data_crawl['comments']= 0
                            data_crawl['views'] = 0
                        li_element = article.query_selector('li.u-concealed')
                        a_element = li_element.query_selector( 'a')
                        href = a_element.get_attribute('href')
                        data_crawl['link']='https://voz.vn'+href
                        time_element = a_element.query_selector('time')
                        datetime_value = time_element.get_attribute('data-time')
                        data_crawl['created_time']=int(datetime_value)

                        
                        try:
                            href = article.query_selector('.reactionsBar-link').get_attribute('href')
                            url=f'https://voz.vn{href}'
                            thread_reactions = threading.Thread(target=self.get_reactions, args=(url,))
                            thread_reactions.start()
                            thread_reactions.join()
                            reactions_data = self.reactions_queue.get()
                            data_crawl['angry']=int(reactions_data[0])
                            data_crawl['list_angry']=reactions_data[1]
                            data_crawl['like']= int(reactions_data[2])
                            data_crawl['list_like']=reactions_data[3]
                        except:
                            data_crawl['angry']=0
                            data_crawl['list_angry']=[]
                            data_crawl['like']= 0
                            data_crawl['list_like']=[]
                            pass
                        data_crawl['out_links']=[]
                        bbWrapper = article.query_selector("div.bbWrapper")
                        image_extensions = ['.jpeg', '.jpg', '.png', '.gif', '.tiff', '.bmp', '.webp', '.heif', '.heic', '.svg',
                        '.raw', '.cr2', '.nef', '.orf', '.sr2']
                        try:
                            
                            if type=='voz comment':
                                out_links=article.query_selector_all('div.bbWrapper a:not(blockquote a)')
                            else:
                                out_links=article.query_selector_all('div.bbWrapper a')
                            for o in out_links:
                                o_href = o.get_attribute('href') if o.get_attribute('href') is not None else ''
                                if ('/goto/post' not in o_href) and (not any(o_href.endswith(ext) for ext in image_extensions)):
                                    data_crawl['out_links'].append(o_href)
                        except:
                            pass
                        data_crawl['out_links'] = [x for x in data_crawl['out_links'] if x is not None and x != '']
                        #Lấy link video của post hoặc comment nếu có
                        data_crawl['videos']=[]
                        try:
                            video_element = bbWrapper.query_selector_all('div.bbMediaWrapper-inner')
                            for v in video_element:
                                iframes = v.query_selector_all('iframe')
                                for i in iframes:
                                    video_link=i.get_attribute('src')
                                    data_crawl['videos'].append(video_link)
                            data_crawl['videos'] = [x for x in data_crawl['videos'] if x is not None and x != '']
                        except:
                            pass
                        try: 
                            blockquote = bbWrapper.query_selector('blockquote.bbCodeBlock.bbCodeBlock--expandable.bbCodeBlock--quote.js-expandWatch')
                            data_attributes =blockquote.get_attribute('data-attributes')
                        except:
                            data_attributes=''
                        if data_attributes!='':
                                data_sources_list = []
                                # img_attributes_list = extract_images_within_blockquotes(bbWrapper)
                                text_after_blockquotes = article.evaluate(
                                            """(article) => {
                                                const blockquotes = article.querySelectorAll('blockquote');
                                                let texts = [];
                                                blockquotes.forEach((bq, index) => {
                                                    let textContent = '';
                                                    let nextNode = bq.nextSibling;
                                                    while(nextNode && (index === blockquotes.length - 1 || nextNode !== blockquotes[index + 1])) {
                                                        if(nextNode.nodeType === Node.TEXT_NODE) {
                                                            textContent += nextNode.textContent.trim();
                                                        } else if (nextNode.tagName === 'BR') {
                                                            textContent += '\\n'; 
                                                        }
                                                        nextNode = nextNode.nextSibling;
                                                    }
                                                    if(textContent) {
                                                        texts.push(textContent);
                                                    }
                                                });
                                                return texts;
                                            }""")
                                data_sources = article.evaluate(
                                            """(article) => {
                                                    const blockquotes = article.querySelectorAll('blockquote');
                                                    return Array.from(blockquotes).map(bq => bq.getAttribute('data-source'));
                                                }
                                            """)
                                data_sources_list.append(data_sources)
                                
                                img_attributes_array = article.evaluate(
                                        """(article) => {
                                            const blockquotes = article.querySelectorAll('blockquote');
                                            let srcList = [];
                                            for (let i = 0; i < blockquotes.length; i++) {
                                                let nextElem = blockquotes[i].nextElementSibling;
                                                let stopAtNextBlockquote = i + 1 < blockquotes.length ? blockquotes[i + 1] : null;
                                                while (nextElem && nextElem !== stopAtNextBlockquote) {
                                                    if (nextElem.matches('div') && nextElem.getAttribute('data-src')) {
                                                        srcList.push('https://voz.vn'+nextElem.getAttribute('data-src'));
                                                    } 
                                                    else if (nextElem.matches('img') && nextElem.getAttribute('src')) {
                                                        srcList.push(nextElem.getAttribute('src'));
                                                    }
                                                    nextElem = nextElem.nextElementSibling;
                                                }
                                            }
                                            return srcList;
                                        }""")
                                #img_attributes_list.append(img_attributes_array)
                                for i in range(1, len(data_sources)):
                                    if data_sources[i] == '':
                                        data_sources[i] = data_sources[i-1]
                                for item1, item2 in zip(text_after_blockquotes, data_sources):
                                            id_root_comment= 'js-post-'+str(item2).split(' ')[1]+'.'
                                            data_crawl['content'] = str(item1).replace('\n\xa0', '').replace("Click to expand...", "")
                                            data_crawl['id']=id_root_comment+id_post
                                            data_crawl['image_url']=img_attributes_array
                                            self.save_data(data_crawl)
                        else:
                            data_crawl['id']=id_post
                            user_post = article.query_selector('div.message-userContent.lbContainer.js-lbContainer')
                            data_crawl['content']= user_post.inner_text().replace('\n\xa0', '').replace("Click to expand...", "")
                            data_crawl['image_url']=[]
                            try:
                                expand_images=article.query_selector_all('div.bbImageWrapper.js-lbImage')
                                for a in expand_images:
                                        link=a.get_attribute('data-src')
                                        try:
                                            new_link=link.split('?image=')[-1]
                                            clean_link=urllib.parse.unquote(new_link.split('&')[0])
                                            data_crawl['image_url'].append(clean_link)
                                        except:
                                            data_crawl['image_url'].append(link)
                                            pass
                                        
                            except:
                                img_elements = user_post.query_selector_all('img')
                                for img_element in img_elements:
                                    src = img_element.get_attribute('src')
                                    data_url = img_element.get_attribute('data-url')
                                    try:
                                        src_split=src.split('?image=')[-1]
                                        clean_link=urllib.parse.unquote(src.split('&')[0])
                                        data_crawl['image_url'].append(src_split)
                                    except:
                                        data_crawl['image_url'].append(src)
                                        pass
                                pass
                            data_crawl['image_url'] = [x for x in data_crawl['image_url'] if x is not None and x != '']
                            self.save_data(data_crawl)
                    page_num += 1  
                    with open('link.txt', 'a', encoding='utf-8') as file:
                        file.write(url)
                    # ChromiumBrowser.stop_playwright()
                    chromium.close()
                    time.sleep(2)
                 # Sleep một chút giữa mỗi lần get để mô phỏng quá trình thực tế
            else:
                # Nếu queue rỗng, chờ đên khi có phần tử mới được thêm vào
                time.sleep(10)
            
    def save_data(self,data):
        with open('voz.txt','a',encoding='utf8') as file:
                    file.write(f'{data}\n')
                    file.close()

    def get_reactions(self,url):
        list_angry=[]
        list_like=[]
        while True:
            print("Processing get reactions of post .....")
            chromium=ChromiumBrowser(fake=self.fake, proxy=self.proxy_post,reset=self.reset)
            chromium.page.goto(url,timeout=600000)
            chromium.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            chromium.page.wait_for_timeout(2000)
            try:
                next_element=chromium.page.query_selector('span.block-footer-controls')
                a_element=next_element.query_selector('a')
                next_link = f"https://voz.vn{a_element.get_attribute('href')}"
                
            except:
                next_link = ''
            url = next_link
            elements = chromium.page.query_selector_all('li.block-row.block-row--separated')
            for e in elements:
                user={}
                avatar_element = e.query_selector('.avatar.avatar--s')
                user_id = avatar_element.get_attribute('data-user-id')
                link_user = f"https://voz.vn{avatar_element.get_attribute('href')}"
                img = avatar_element.query_selector('img')
                if img:
                        src = img.get_attribute('src')
                        name = img.get_attribute('alt')
                else:
                    src=''
                    span = avatar_element.query_selector('span')
                    name = span.get_attribute('aria-label')

                div_element = e.query_selector('div.contentRow-extra')
                span_element = div_element.query_selector('span')
                reaction_id = span_element.get_attribute('data-reaction-id')
                time_element = div_element.query_selector('time')
                reacted_time = time_element.get_attribute('data-time')

                div_element_2 = e.query_selector('div.contentRow-lesser')
                role_element = div_element_2.query_selector('span.userTitle')
                role = role_element.inner_text()
                try:
                    loaction_element = div_element_2.query_selector('a')
                    link_location = 'https://voz.vn'+loaction_element.get_attribute('href')
                    location = loaction_element.inner_text() 
                except:
                    link_location=''
                    location=''
                    pass

                div_element_3 = e.query_selector('div.contentRow-minor')
                li_elements = div_element_3.query_selector_all('li')
                str_number=''
                for li in li_elements:
                    dl_element= li.query_selector('dl.pairs.pairs--inline')
                    dd_element = dl_element.query_selector('dd')
                    number = dd_element.inner_text()+'|'
                    str_number+=number
                user['author'] = name
                user['id']= user_id
                user['role']= role
                user['author_link']= link_user
                user['avatar']= src
                user['location']= location
                user['location_link']=link_location
                user['messages']=float(str_number.split('|')[0].replace(',','.'))
                user['reactions_points'] = float(str_number.split('|')[1].replace(',','.'))
                user['points'] = int(str_number.split('|')[2])
                user['reacted_time']=int(reacted_time)
                if reaction_id=='1':
                    list_like.append(user)
                elif reaction_id=='2':
                    list_angry.append(user)
            if next_link=='': 
                chromium.close()
                break
            chromium.close()
            time.sleep(5)
        reactions_data = (len(list_angry), list_angry, len(list_like), list_like)
        self.reactions_queue.put(reactions_data)
    

    def convert_unit_to_num(self,txt):
        numbers = (re.findall(r'\d+', txt))[0]
        try:
            words = (re.findall(r'[a-zA-Z]+', txt))[0]
        except:
            words=''
        if words == 'K':
            return int(float(numbers) * 1000)
        elif words == 'M':
            return int(float(numbers) * 1000000)
        elif words == 'B':
            return int(float(numbers) * 1000000000)
        else:
            return int(numbers)

    def get_link(self,url):
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        midnight_timestamp = int(today.timestamp())
        page_num = 0
        path_crawled='link.txt'
        path_black_link='black_list.txt'
        with open(path_crawled, 'r') as file:
            lines = file.readlines()
        link_crawled=[line.strip() for line in lines]
        with open(path_black_link, 'r') as file:
            line_ = file.readlines()
        black_list=[line.strip() for line in line_]
        chromium2=ChromiumBrowser(fake=self.fake, proxy=self.proxy_post,reset=self.reset)
        next_link=''
        while next_link!=None:
            if page_num > 0:
                url = next_link
            chromium2.page.goto(url,timeout=600000)
            try:
                next_link =  chromium2.page.eval_on_selector('a.pageNav-jump.pageNav-jump--next', 'a => a.href')
            except:
                next_link = None
            # div_elements_1 = chromium2.page.query_selector_all('div.structItemContainer-group.structItemContainer-group--sticky > div')
            # div_elements_2 = chromium2.page.query_selector_all('div.structItemContainer-group.js-threadList > div')
            # div_elements = div_elements_1 + div_elements_2
            div_elements = div_elements = chromium2.page.query_selector_all('div.structItemContainer > div')
            for div in div_elements:
                reaction_txt=str(div.query_selector("div.structItem-cell.structItem-cell--meta").text_content()).split('\n')
                comment=self.convert_unit_to_num(str(reaction_txt[3]))
                views=self.convert_unit_to_num(str(reaction_txt[7]))
                a_element = div.query_selector_all('div.structItem-title a')[-1]
                li_element = div.query_selector('li.structItem-startDate')
                time_element =  li_element.query_selector('time')
                time_=int(time_element.get_attribute('data-time'))
                href='https://voz.vn'+a_element.get_attribute('href')
                if href not in link_crawled and href not in black_list and  time_>=midnight_timestamp:
                    link = f'{href}|{comment}|{views}'
                    print(f'---------->>>>>>>>> Put {link} to Queue')
                    self.link_queue.put(link)
            page_num += 1
            time.sleep(10)
        chromium2.close()


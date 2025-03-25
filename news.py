import requests
from bs4 import BeautifulSoup

url = "https://www.anyang.ac.kr/main/communication/school-news.do?mode=list&&articleLimit=700"
url_main = "https://www.anyang.ac.kr/main/communication/school-news.do"

html_text = requests.get(url)

html = BeautifulSoup(html_text.text, "html.parser")
html_news = html.select('#cms-content > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr')

news_list = []

for i in range(len(html_news) - 1, 0, -1):
    news = html.select(f'#cms-content > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr:nth-child({i})')

    if news:
        news = news[0]
        news_ID = news.select_one("td.b-num-box").text.strip()

        title_element = news.select_one('td.b-td-left.b-td-title > div > a')
        title = title_element.get('title') if title_element else "No title"
        title = title.replace(" 자세히 보기", "")
        link_add = title_element.get("href") if title_element else "#"
        link = url_main + link_add

        writer = news.select_one('td:nth-child(3)').text.strip() if news.select_one('td:nth-child(3)') else "No writer"
        date = news.select_one('td:nth-child(4)').text.strip() if news.select_one('td:nth-child(4)') else "No date"
        views = news.select_one('td:nth-child(5)').text.strip() if news.select_one('td:nth-child(5)') else "No views"

        try:
            html_text_2 = requests.get(link)
            html_2 = BeautifulSoup(html_text_2.text, "html.parser")

            download_html = html_2.select_one(".b-file-box > ul")
            if download_html:
                download_items = download_html.find_all('li')
                download_link = ''
                download_title = ''
                for item in download_items:
                    a_tag = item.find('a')
                    if a_tag:
                        download_link = url_main + a_tag['href'] + ', ' + download_link
                        download_title = a_tag.text.strip() + ', ' + download_title
            else:
                download_link = ''
                download_title = ''

            body = html_2.select_one(".b-content-box > .fr-view")

        except requests.RequestException as e:
            print(f"Error fetching {link}: {e}")

        news_list.append({
            "Id" : news_ID,
            "newsTitle": str(title),
            "newsWriter": str(writer),
            "newsLink": str(link),
            "newsDate": str(date),
            "newsViews": str(views),
            "newsBody" : str(body),
            "newsDownloadLink": str(download_link),
            "newsDownloadTitle" : str(download_title)
        })

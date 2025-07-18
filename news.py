import requests
from bs4 import BeautifulSoup

url = "https://www.anyang.ac.kr/main/communication/school-news.do?mode=list&&articleLimit=6"
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
        # link = url_main + link_add  # newsLink 값 주석 처리

        writer = news.select_one('td:nth-child(3)').text.strip() if news.select_one('td:nth-child(3)') else "No writer"
        date = news.select_one('td:nth-child(4)').text.strip() if news.select_one('td:nth-child(4)') else "No date"

        try:
            # link 변수를 쓴 부분이 있으니, link 변수가 필요하면 따로 처리해야 합니다.
            # 여기서는 link 대신 link_add를 그대로 씁니다.
            html_text_2 = requests.get(url_main + link_add)
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

            body = html_2.select_one(".b-content-box")

        except requests.RequestException as e:
            print(f"Error fetching {url_main + link_add}: {e}")

        news_list.append({
            "id" : news_ID,
            "newsTitle": str(title),
            "newsWriter": str(writer),
            # "newsLink": str(link),  # newsLink 값 주석 처리
            "newsDate": str(date),
            "newsBody" : str(body),
            "newsDownloadLink": str(download_link),
            "newsDownloadTitle" : str(download_title)
        })

api_url = "https://doyouknow.shop/news/addNews"
response = requests.post(api_url, json=news_list)

if response.status_code == 201:
    print("Notices successfully added.")
else:
    print("Failed to add notices.")

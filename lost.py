import requests
from bs4 import BeautifulSoup

url = "https://www.anyang.ac.kr/main/communication/lost-found.do?mode=list&&articleLimit=200"
url_main = "https://www.anyang.ac.kr/main/communication/lost-found.do"

html_text = requests.get(url)

html = BeautifulSoup(html_text.text, "html.parser")
html_lost = html.select('#cms-content > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr')

lost_list = []

for i in range(len(html_lost) - 1, 0, -1):
    lost = html.select(f'#cms-content > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr:nth-child({i})')

    if lost:
        lost = lost[0]
        lost_ID = lost.select_one("td.b-num-box").text.strip()

        title_element = lost.select_one('td.b-td-left.b-td-title > div > a')
        title = title_element.get('title') if title_element else "No title"
        title = title.replace(" 자세히 보기", "")
        link_add = title_element.get("href") if title_element else "#"
        link = url_main + link_add

        writer = lost.select_one('td:nth-child(3)').text.strip() if lost.select_one('td:nth-child(3)') else "No writer"
        date = lost.select_one('td:nth-child(4)').text.strip() if lost.select_one('td:nth-child(4)') else "No date"
        views = lost.select_one('td:nth-child(5)').text.strip() if lost.select_one('td:nth-child(5)') else "No views"

        try:
            html_text_2 = requests.get(link)
            html_2 = BeautifulSoup(html_text_2.text, "html.parser")
            body = html_2.select_one(".b-content-box")

        except requests.RequestException as e:
            print(f"Error fetching {link}: {e}")

        lost_list.append({
            "Id" : lost_ID,
            "lostTitle": str(title),
            "lostWriter": str(writer),
            "lostLink": str(link),
            "lostDate": str(date),
            "lostViews": str(views),
            "lostBody" : str(body),
        })

import requests
from bs4 import BeautifulSoup


url = "https://www.anyang.ac.kr/main/communication/notice.do?mode=list&&articleLimit=5&article.offset=0"
url_main = "https://www.anyang.ac.kr/main/communication/notice.do"

html_text = requests.get(url)

html = BeautifulSoup(html_text.text, "html.parser")
html_notice = html.select("#cms-content > div > div > div.bn-list-common01.type01.bn-common-cate > table > tbody > tr")

notice_list = []

for i in range(len(html_notice) - 1, 0, -1):
    notice = html.select(f"#cms-content > div > div > div.bn-list-common01.type01.bn-common-cate > table > tbody > tr:nth-child({i})")
    if notice:
        notice = notice[0]

        title_element = notice.select_one("td.b-td-left.b-td-title > div > a")
        title = title_element.get("title") if title_element else "No title"
        title = title.replace(" 자세히 보기", "")
        link_add = title_element.get("href") if title_element else "#"
        link = url_main + link_add

        parts = link_add.split("&")
        for part in parts:
            if "articleNo=" in part:
                articleId = part.split("=")[1]
                break

        category = notice.select_one("td.b-cate-box").text.strip() if notice.select_one("td.b-cate-box") else "No category"
        writer = notice.select_one("td:nth-child(4)").text.strip() if notice.select_one("td:nth-child(4)") else "No writer"
        date = notice.select_one("td:nth-child(5)").text.strip() if notice.select_one("td:nth-child(5)") else "No date"

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

            body = html_2.select_one(".b-content-box")

        except requests.RequestException as e:
            print(f"Error fetching {link}: {e}")

        notice_list.append({
            "id" : articleId,
            "noticeTitle": str(title),
            "noticeWriter": str(writer),
            "noticeLink": str(link),
            "noticeDate": str(date),
            "noticeCategory": str(category),
            "noticeBody" : str(body),
            "noticeDownloadLink" : str(download_link),
            "noticeDownloadTitle" : str(download_title)
        })

api_url = "https://doyouknow.shop/notice/addNotice"
response = requests.post(api_url, json=notice_list)

if response.status_code == 201:
    print("Notices successfully added.")
else:
    print("Failed to add notices.")

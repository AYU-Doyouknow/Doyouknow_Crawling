import requests
from bs4 import BeautifulSoup


url = "https://www.anyang.ac.kr/main/communication/notice.do?mode=list&&articleLimit=10000&article.offset=1"
url_main = "https://www.anyang.ac.kr/main/communication/notice.do"

# Send a request to the website and get the HTML content
html_text = requests.get(url)

# Parse the content with BeautifulSoup
html = BeautifulSoup(html_text.text, "html.parser")
html_notice = html.select("#cms-content > div > div > div.bn-list-common01.type01.bn-common-cate > table > tbody > tr")

notice_list = []

for i in range(0,len(html_notice)):
    notice = html.select(f"#cms-content > div > div > div.bn-list-common01.type01.bn-common-cate > table > tbody > tr:nth-child({i})")
    if notice:
        notice = notice[0]
        
        noticeCheck = notice.select_one("td.b-num-box.b-notice")
        if noticeCheck:
            noticeCheck = True
        else:
            noticeCheck = False
        print(noticeCheck)

        title_element = notice.select_one("td.b-td-left.b-td-title > div > a")
        title = title_element.get("title") if title_element else "No title"
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
        views = notice.select_one("td:nth-child(6)").text.strip() if notice.select_one("td:nth-child(6)") else "No views"

        try:
            html_text_2 = requests.get(link)
            html_2 = BeautifulSoup(html_text_2.text, "html.parser")

            download_html = html_2.select_one(".b-file-box > ul")
            if download_html:
                download = download_html
            else:
                download = ''

            body_html = html_2.select_one(".b-content-box > .fr-view")
            if body_html:
                body = str(body_html)

        except requests.RequestException as e:
            print(f"Error fetching {link}: {e}")

        notice_list.append({
            "Id" : articleId,
            "noticeCheck" : str(noticeCheck),
            "noticeTitle": str(title),
            "noticeDormitory": str(writer),
            "noticeLink": str(link),
            "noticeDate": str(date),
            "noticeCategory": str(category),
            "noticeViews": str(views),
            "noticeBody" : str(body),
            "noticeDownload" : str(download)
        })
        print(notice_list)
    else:
        print(f"No notice found at row {i}")



# api_url = "http://localhost:8080/notices/add"
# response = requests.post(api_url, json=notice_list)

# if response.status_code == 200:
#     print("Notices successfully added.")
# else:
#     print("Failed to add notices.")

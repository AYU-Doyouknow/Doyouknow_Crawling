import requests
from bs4 import BeautifulSoup
import mysql.connector

url_main = "https://www.anyang.ac.kr/main/communication/notice.do"
notice_list = []

# DB 연결
conn = mysql.connector.connect(
    host="퍼블릭 IP",
    user="root",
    password="비밀번호",
    database="doyouknow",
)
cursor = conn.cursor()

# 100개씩 100페이지 순회 (0 ~ 9900)
for offset in range(0, 10000, 100):
    url = f"https://www.anyang.ac.kr/main/communication/notice.do?mode=list&&articleLimit=100&article.offset={offset}"
    html_text = requests.get(url)
    html = BeautifulSoup(html_text.text, "html.parser")
    html_notice = html.select("#cms-content > div > div > div.bn-list-common01.type01.bn-common-cate > table > tbody > tr")

    for i in range(len(html_notice), 0, -1):
        notice = html.select(f"#cms-content > div > div > div.bn-list-common01.type01.bn-common-cate > table > tbody > tr:nth-child({i})")
        if notice:
            notice = notice[0]

            title_element = notice.select_one("td.b-td-left.b-td-title > div > a")
            title = title_element.get("title") if title_element else "No title"
            title = title.replace(" 자세히 보기", "")
            link_add = title_element.get("href") if title_element else "#"
            link = url_main + link_add

            parts = link_add.split("&")
            articleId = None
            for part in parts:
                if "articleNo=" in part:
                    articleId = part.split("=")[1]
                    break

            writer = notice.select_one("td:nth-child(4)").text.strip() if notice.select_one("td:nth-child(4)") else "No writer"
            date = notice.select_one("td:nth-child(5)").text.strip() if notice.select_one("td:nth-child(5)") else "No date"

            try:
                html_text_2 = requests.get(link)
                html_2 = BeautifulSoup(html_text_2.text, "html.parser")

                download_html = html_2.select_one(".b-file-box > ul")
                download_link = ''
                download_title = ''
                if download_html:
                    download_items = download_html.find_all('li')
                    for item in download_items:
                        a_tag = item.find('a')
                        if a_tag:
                            download_link = url_main + a_tag['href'] + ', ' + download_link
                            download_title = a_tag.text.strip() + ', ' + download_title
                body = html_2.select_one(".b-content-box")

            except requests.RequestException as e:
                print(f"Error fetching {link}: {e}")
                continue

            # INSERT 쿼리
            cursor.execute("""
                INSERT INTO notice (id, notice_title, notice_writer, notice_date, notice_download_link, notice_download_title, notice_body)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    notice_title = VALUES(notice_title),
                    notice_writer = VALUES(notice_writer),
                    notice_date = VALUES(notice_date),
                    notice_download_link = VALUES(notice_download_link),
                    notice_download_title = VALUES(notice_download_title),
                    notice_body = VALUES(notice_body)
            """, (
                int(articleId),
                title,
                writer,
                date,
                download_link,
                download_title,
                str(body)
            ))

conn.commit()
cursor.close()
conn.close()
print("데이터 저장 완료.")
import requests
from bs4 import BeautifulSoup
import mysql.connector

url = "https://www.anyang.ac.kr/main/communication/lost-found.do?mode=list&&articleLimit=30"
url_main = "https://www.anyang.ac.kr/main/communication/lost-found.do"

html_text = requests.get(url)
html = BeautifulSoup(html_text.text, "html.parser")
html_lost = html.select('#cms-content > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr')

# DB 연결
conn = mysql.connector.connect(
    host="퍼블릭 ip",
    user="root",
    password="비밀번호",  
    database="doyouknow"
)
cursor = conn.cursor()

for i in range(len(html_lost) - 1, 0, -1):
    lost = html.select(f'#cms-content > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr:nth-child({i})')

    if lost:
        lost = lost[0]
        lost_ID = int(lost.select_one("td.b-num-box").text.strip())

        title_element = lost.select_one('td.b-td-left.b-td-title > div > a')
        title = title_element.get('title').replace(" 자세히 보기", "") if title_element else "No title"
        link_add = title_element.get("href") if title_element else "#"
        link = url_main + link_add

        writer = lost.select_one('td:nth-child(3)').text.strip()
        date = lost.select_one('td:nth-child(4)').text.strip()

        # 상세 내용 크롤링
        try:
            html_text_2 = requests.get(link)
            html_2 = BeautifulSoup(html_text_2.text, "html.parser")
            body = html_2.select_one(".b-content-box")
        except requests.RequestException as e:
            print(f"Error fetching {link}: {e}")
            body = None

        # INSERT 쿼리
        cursor.execute("""
            INSERT INTO lost (id, lost_title, lost_writer, lost_date, lost_body)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                lost_title=VALUES(lost_title),
                lost_writer=VALUES(lost_writer),
                lost_date=VALUES(lost_date),
                lost_body=VALUES(lost_body)
        """, (lost_ID, title, writer, date, str(body)))

conn.commit()
cursor.close()
conn.close()

print("데이터 저장 완료.")
import time

print("=== 스크립트 시작 ===")

# ===== IMPORT 체크 =====
print("Imports 체크 중...")

try:
    import requests
    print("requests OK")
except Exception as e:
    print("❌ requests import 오류:", e)
    raise

try:
    from bs4 import BeautifulSoup
    print("bs4 OK")
except Exception as e:
    print("❌ bs4 import 오류:", e)
    raise

try:
    import pymysql
    print("pymysql OK")
except Exception as e:
    print("❌ pymysql import 오류:", e)
    raise

print("=== 모든 import 완료 ===\n")


# ===== 기본 설정 =====
BASE_URL = "https://www.anyang.ac.kr"
LIST_URL = f"{BASE_URL}/main/communication/school-news.do"


# ===== DB 연결 =====
print("DB 연결 시도...")

try:
    conn = pymysql.connect(
        host="퍼블릭 IP", 
        user="root",
        password="비밀번호",
        database="doyouknow",
        charset="utf8mb4",
        autocommit=False,
    )
    cursor = conn.cursor()
    print("✅ DB 연결 성공\n")
except Exception as e:
    print("❌ DB 연결 실패:", e)
    raise SystemExit(1)


# ===== HTTP 세션 =====
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; dyk-school-news-crawler/1.0)"
})


# ===== 유틸 함수 =====
def build_full_url(href: str) -> str:
    """상대경로를 절대 URL로 변환"""
    if not href:
        return ""
    href = href.strip()
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE_URL + href
    return LIST_URL + href


print("=== school-news 크롤링 시작 ===")

try:
    # 리스트 요청
    params = {
        "mode": "list",
        "articleLimit": 700,
    }

    print(f"[LIST 요청] {LIST_URL} / params={params}")

    resp = session.get(LIST_URL, params=params, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select(
        "#cms-content > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr"
    )

    print(f"→ rows 개수: {len(rows)}")

    if len(rows) == 0:
        print("⚠ rows=0 : 페이지 구조 변경 가능성 있음")

    # 역순 순회
    for idx, row in enumerate(reversed(rows), start=1):
        num_td = row.select_one("td.b-num-box")
        if not num_td:
            continue

        try:
            news_id = int(num_td.get_text(strip=True))
        except ValueError:
            print(f"[SKIP] news_id 파싱 실패: '{num_td.get_text(strip=True)}'")
            continue

        # 제목
        title_el = row.select_one("td.b-td-left.b-td-title > div > a")
        if not title_el:
            print(f"[SKIP] id={news_id}: 제목 없음")
            continue

        raw_title = title_el.get("title") or title_el.get_text(strip=True)
        title = raw_title.replace(" 자세히 보기", "").strip()

        href = title_el.get("href") or ""
        news_url = build_full_url(href)

        writer_td = row.select_one("td:nth-child(3)")
        date_td = row.select_one("td:nth-child(4)")

        writer = writer_td.get_text(strip=True) if writer_td else ""
        date = date_td.get_text(strip=True) if date_td else ""

        print(f"[{idx}] id={news_id} / title='{title}' / url={news_url}")

        # 상세 페이지
        try:
            detail_resp = session.get(news_url, timeout=10)
            detail_resp.raise_for_status()
        except Exception as e:
            print(f"  ❌ 상세 요청 실패(id={news_id}): {e}")
            body_html = ""
            download_link = ""
            download_title = ""
        else:
            detail_soup = BeautifulSoup(detail_resp.text, "html.parser")

            # 첨부파일
            download_list = detail_soup.select_one(".b-file-box > ul")
            links = []
            titles = []

            if download_list:
                for item in download_list.find_all("li"):
                    a_tag = item.find("a")
                    if a_tag:
                        file_url = build_full_url(a_tag.get("href", ""))
                        links.append(file_url)
                        titles.append(a_tag.get_text(strip=True))

            download_link = ", ".join(links)
            download_title = ", ".join(titles)

            # 본문
            body = detail_soup.select_one(".b-content-box")
            body_html = str(body) if body else ""

        # ===== DB 저장 (news_link 제거됨) =====
        try:
            cursor.execute(
                """
                INSERT INTO news (
                    id,
                    news_title,
                    news_writer,
                    news_date,
                    news_body,
                    news_download_link,
                    news_download_title,
                    news_url
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    news_title = VALUES(news_title),
                    news_writer = VALUES(news_writer),
                    news_date = VALUES(news_date),
                    news_body = VALUES(news_body),
                    news_download_link = VALUES(news_download_link),
                    news_download_title = VALUES(news_download_title),
                    news_url = VALUES(news_url)
                """,
                (
                    news_id,
                    title,
                    writer,
                    date,
                    body_html,
                    download_link,
                    download_title,
                    news_url,
                ),
            )
        except Exception as e:
            print(f"    ❌ DB 저장 실패(id={news_id}): {e}")
            continue

    conn.commit()
    print("\n✅ 커밋 완료")

finally:
    cursor.close()
    conn.close()
    print("=== 크롤링 종료 / 커넥션 정리 완료 ===")

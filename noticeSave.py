import time

print("=== notice 전체 크롤링 + notice_url 저장 스크립트 시작 ===")

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
LIST_URL = f"{BASE_URL}/main/communication/notice.do"

print(f"BASE_URL = {BASE_URL}")
print(f"LIST_URL = {LIST_URL}\n")


# ===== DB 연결 (pymysql) =====
print("DB 연결 시도...")

try:
    conn = pymysql.connect(
        host="퍼블릭ip",
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
    print("프로그램 종료")
    raise SystemExit(1)


# ===== HTTP 세션 =====
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; dyk-notice-full-crawler/1.0)"
})


# ===== 유틸 함수 =====
def build_full_url(href: str) -> str:
    """상대경로 href를 절대 URL로 변환"""
    if not href:
        return ""
    href = href.strip()
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE_URL + href
    return LIST_URL + href


def extract_article_id(href: str):
    """href 에서 articleNo 추출"""
    if not href:
        return None
    for part in href.split("&"):
        if "articleNo=" in part:
            try:
                return int(part.split("=")[1])
            except ValueError:
                return None
    return None


print("=== notice 전체 크롤링 시작 ===\n")

total_insert_or_update = 0

try:
    # 100개씩 100페이지 순회 (0 ~ 6900)
    for offset in range(0, 6900, 100):
        print(f"[LIST 요청] offset={offset}")

        params = {
            "mode": "list",
            "articleLimit": 100,
            "article.offset": offset,
        }

        # 리스트 페이지 요청
        try:
            resp = session.get(LIST_URL, params=params, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"  ❌ 리스트 요청 실패 (offset={offset}): {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # 너무 구체적인 셀렉터보다는 약간 느슨하게
        rows = soup.select("#cms-content table tbody tr")
        print(f"  → rows 개수: {len(rows)}")

        if not rows:
            print("  ⚠ rows=0 : 페이지 구조가 달라졌거나, 더 이상 데이터가 없을 수 있음.")
            continue

        processed_in_page = 0

        # 역순 순회 (이전 코드 스타일 유지)
        for row in reversed(rows):
            title_element = row.select_one("td.b-td-left.b-td-title > div > a")
            if not title_element:
                # 공지 헤더 같은 특수행일 수 있음
                continue

            # 제목
            raw_title = title_element.get("title") or title_element.get_text(strip=True)
            title = raw_title.replace(" 자세히 보기", "").strip()

            # 링크 / articleId
            href = title_element.get("href", "")
            notice_url = build_full_url(href)   # <= 이걸 notice_url 컬럼에 저장

            article_id = extract_article_id(href)
            if not article_id:
                print(f"    [SKIP] articleNo 추출 실패 href={href}")
                continue

            # 작성자 / 날짜
            writer_td = row.select_one("td:nth-child(4)")
            date_td = row.select_one("td:nth-child(5)")

            writer = writer_td.get_text(strip=True) if writer_td else ""
            date = date_td.get_text(strip=True) if date_td else ""

            # ===== 상세 페이지 요청 =====
            try:
                detail_resp = session.get(notice_url, timeout=10)
                detail_resp.raise_for_status()
            except Exception as e:
                print(f"    ❌ 상세 요청 실패 (id={article_id}, url={notice_url}): {e}")
                continue

            detail_soup = BeautifulSoup(detail_resp.text, "html.parser")

            # 첨부파일
            download_html = detail_soup.select_one(".b-file-box > ul")
            download_link = ""
            download_title = ""

            if download_html:
                download_items = download_html.find_all("li")
                links = []
                titles = []
                for item in download_items:
                    a_tag = item.find("a")
                    if not a_tag:
                        continue
                    file_href = a_tag.get("href", "")
                    file_url = build_full_url(file_href)
                    links.append(file_url)
                    titles.append(a_tag.get_text(strip=True))

                download_link = ", ".join(links)
                download_title = ", ".join(titles)

            # 본문
            body = detail_soup.select_one(".b-content-box")
            body_html = str(body) if body else ""

            # ===== DB INSERT / UPDATE =====
            try:
                cursor.execute(
                    """
                    INSERT INTO notice (
                        id,
                        notice_title,
                        notice_writer,
                        notice_date,
                        notice_download_link,
                        notice_download_title,
                        notice_body,
                        notice_url
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        notice_title = VALUES(notice_title),
                        notice_writer = VALUES(notice_writer),
                        notice_date = VALUES(notice_date),
                        notice_download_link = VALUES(notice_download_link),
                        notice_download_title = VALUES(notice_download_title),
                        notice_body = VALUES(notice_body),
                        notice_url = VALUES(notice_url)
                    """,
                    (
                        article_id,
                        title,
                        writer,
                        date,
                        download_link,
                        download_title,
                        body_html,
                        notice_url,
                    ),
                )
                processed_in_page += 1
                total_insert_or_update += 1
            except Exception as e:
                print(f"    ❌ DB INSERT/UPDATE 실패 (id={article_id}): {e}")
                continue

        conn.commit()
        print(f"  → offset={offset} 커밋 완료 (처리된 게시글 수: {processed_in_page})\n")

        time.sleep(0.3)

finally:
    cursor.close()
    conn.close()
    print(f"\n=== 전체 작업 완료 (총 처리된 게시글 수: {total_insert_or_update}) ===")
    print("커넥션 정리 완료")

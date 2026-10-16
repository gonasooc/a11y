"""Collect the 2012-2016 KMCC press-release HWP files with broadcaster-level disability-broadcast results."""

from __future__ import annotations

import argparse
import hashlib
import html
import http.cookiejar
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
HOST = "www.kmcc.go.kr"
LIST_URL = "https://www.kmcc.go.kr/user.do?page=A05030000&dc=K00000200&boardId=1113"
VIEW_URL = "https://www.kmcc.go.kr/user.do?mode=view&page=A05030000&dc=K00000200&boardId=1113&boardSeq={board_seq}"
DOWNLOAD_URL = "https://www.kmcc.go.kr/download.do?fileSeq={file_seq}"
USER_AGENT = "a11y-research/1.0 (+https://github.com/gonasooc/a11y)"
# 실적연도, 게시물 번호, 첨부 번호, 역할. 2015·2016년은 본문과 방송사별 표(붙임)가 따로 있다.
SOURCES = (
    (2012, 36057, 37195, "body_and_table"),
    (2013, 38640, 39231, "body_and_table"),
    (2014, 41299, 41412, "body_and_table"),
    (2015, 42607, 43407, "body"), (2015, 42607, 43408, "table"),
    (2016, 44899, 45170, "body"), (2016, 44899, 45172, "table"),
)
TITLE = re.compile(r'<td colspan="3" class="table_title">\s*((20\d\d)년도? 장애인방송 제공실적 평가결과)\s*</td>')
POSTED = re.compile(r'등록일</th>\s*<td class="txtL">(\d{4}-\d{2}-\d{2})</td>')
ATTACHMENT = re.compile(
    r'href="/download\.do[^"?]*\?fileSeq=(\d+)" title="파일 다운로드">.*?<span class="font_56">([^<]+)</span>', re.S)
OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
DELAY_SECONDS = 1.0


class CollectError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # 세션 없이 받으면 오류 페이지로 넘어간다. 넘어가지 않고 멈춘다.
        raise CollectError(f"예상하지 못한 리다이렉트: {newurl}")


class Client:
    def __init__(self):
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect())
        self.last = 0.0

    def get(self, url: str, referer: str | None = None) -> bytes:
        if urllib.parse.urlsplit(url).hostname != HOST:
            raise CollectError(f"허용하지 않은 호스트: {url}")
        wait = DELAY_SECONDS - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        headers = {"User-Agent": USER_AGENT, **({"Referer": referer} if referer else {})}
        try:
            with self.opener.open(urllib.request.Request(url, headers=headers), timeout=60) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            raise CollectError(f"HTTP {exc.code}: {url}") from None
        self.last = time.monotonic()
        return body


def one(pattern: re.Pattern, text: str, what: str) -> re.Match:
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise CollectError(f"{what}를 하나로 찾지 못했다({len(matches)}개)")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    client, files, pages = Client(), [], {}
    raw_dir = HERE / "raw" / "kmcc"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for year, board_seq, file_seq, role in SOURCES:
        view_url = VIEW_URL.format(board_seq=board_seq)
        if board_seq not in pages:
            # 첨부는 같은 세션으로 게시물을 먼저 연 뒤에만 받을 수 있다.
            page = client.get(view_url).decode("utf-8", "replace")
            title = one(TITLE, page, f"{board_seq} 제목")
            if int(title.group(2)) != year:
                raise CollectError(f"{board_seq}: 제목 연도가 {year}가 아니다")
            pages[board_seq] = {
                "title": title.group(1), "posted_date": one(POSTED, page, f"{board_seq} 등록일").group(1),
                "attachments": {int(seq): html.unescape(name).strip() for seq, name in ATTACHMENT.findall(page)},
            }
        post = pages[board_seq]
        if file_seq not in post["attachments"]:
            raise CollectError(f"{board_seq}: 첨부 {file_seq}가 게시물에 없다")
        body = client.get(DOWNLOAD_URL.format(file_seq=file_seq), referer=view_url)
        if body[:8] != OLE_MAGIC:
            raise CollectError(f"{year} {file_seq}: HWP(OLE) 파일이 아니다")
        path = raw_dir / f"kmcc_{year}_{file_seq}.hwp"
        path.write_bytes(body)
        files.append({
            "year": year, "role": role, "title": post["title"], "posted_date": post["posted_date"],
            "view_url": view_url, "file_seq": file_seq, "file_name": post["attachments"][file_seq],
            "file_size": len(body), "download_url": DOWNLOAD_URL.format(file_seq=file_seq),
            "sha256": hashlib.sha256(body).hexdigest(), "raw_path": str(path.relative_to(HERE)),
        })
        print(f"{year} {file_seq} {post['attachments'][file_seq]} {len(body):,}바이트")
    manifest = {
        "publisher": "방송미디어통신위원회(게시 당시 방송통신위원회)",
        "collection": "보도자료 'YYYY년(도) 장애인방송 제공실적 평가결과'",
        "list_url": LIST_URL, "snapshot": args.snapshot.isoformat(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "access_note": ("robots.txt는 Googlebot에만 /user.do 등을 막고 * 규칙이 없다. 누리집 하단에 이용약관은 없고 "
                        "저작권보호정책에 자동 수집 금지 조항이 없다. 다섯 게시물의 공공누리 유형 칸은 비어 있다(2026-10-17 확인). "
                        "게시물을 먼저 열고 Referer를 붙여 첨부를 받는다. 요청 사이 1초, 원본 HWP는 raw/에 두고 Git에서 제외"),
        "files": files,
    }
    (HERE / "data" / "kmcc_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"파일 {len(files)}개")


if __name__ == "__main__":
    main()

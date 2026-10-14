"""Collect the yearly disability-broadcast results that KCMF publishes as HWPX files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
HOST = "kcmf.or.kr"
LIST_URL = "https://kcmf.or.kr/KCMF/contents/KCMF040201121.do"
VIEW_URL = LIST_URL + "?schM=view&id={post_id}"
FILE_LIST_URL = "https://kcmf.or.kr/afile/fileList.do?fileId={file_id}"
DOWNLOAD_URL = "https://kcmf.or.kr/afile/fileDownload/{file_idx}"
USER_AGENT = "a11y-research/1.0 (+https://github.com/gonasooc/a11y)"
POST_ID = re.compile(r"fn_goView\('([A-Za-z0-9_-]+)'\)")
# 본문 제목만 읽는다. 이전글·다음글 링크에도 다른 연도의 제목이 있다.
TITLE = re.compile(r'<h3 class="headline">\s*((20\d\d)년 장애인방송 편성 실적\(방송사명, 목표, 실적\))\s*</h3>')
FILE_ID = re.compile(r'data:"fileId=(\d+)"')
POSTED = re.compile(r"작성일\s*:\s*(\d{4})\.(\d{2})\.(\d{2})")
FILE_IDX = re.compile(r"[A-Za-z0-9]{1,32}")
DELAY_SECONDS = 1.0


class CollectError(RuntimeError):
    pass


class Client:
    def __init__(self):
        self.last = 0.0

    def get(self, url: str) -> bytes:
        if urllib.parse.urlsplit(url).hostname != HOST:
            raise CollectError(f"허용하지 않은 호스트: {url}")
        wait = DELAY_SECONDS - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=30) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname != HOST:
                raise CollectError(f"예상하지 못한 리다이렉트: {response.geturl()}")
            body = response.read()
        self.last = time.monotonic()
        return body


def one(pattern: re.Pattern, text: str, what: str) -> re.Match:
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise CollectError(f"{what}를 하나로 찾지 못했다({len(matches)}개)")
    return matches[0]


def post_entry(client: Client, post_id: str) -> dict:
    view_url = VIEW_URL.format(post_id=post_id)
    page = client.get(view_url).decode("utf-8", "replace")
    title = one(TITLE, page, "게시물 제목")
    posted = one(POSTED, page, "작성일")
    file_id = one(FILE_ID, page, "첨부 묶음 번호").group(1)
    files = json.loads(client.get(FILE_LIST_URL.format(file_id=file_id)))
    if not isinstance(files, list) or len(files) != 1:
        raise CollectError(f"{title.group(1)}: 첨부 파일이 하나가 아니다")
    meta = files[0]
    if meta.get("ext") != "hwpx" or not FILE_IDX.fullmatch(str(meta.get("fileIdx", ""))):
        raise CollectError(f"{title.group(1)}: 예상한 HWPX 첨부가 아니다")
    return {
        "year": int(title.group(2)),
        "title": title.group(1),
        "posted_date": "-".join(posted.groups()),
        "view_url": view_url,
        "file_id": file_id,
        "file_name": meta["fileName"],
        "file_size": int(meta["fileSize"]),
        "download_url": DOWNLOAD_URL.format(file_idx=meta["fileIdx"]),
    }


def download(client: Client, entry: dict, raw_dir: Path, refresh: bool) -> Path:
    path = raw_dir / f"kcmf_{entry['year']}.hwpx"
    if refresh or not path.exists():
        path.write_bytes(client.get(entry["download_url"]))
    if path.stat().st_size != entry["file_size"]:
        raise CollectError(f"{path.name}: 크기가 목록 API와 다르다")
    if not zipfile.is_zipfile(path):
        raise CollectError(f"{path.name}: HWPX(zip) 형식이 아니다")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=date.fromisoformat, default=date.today(),
                        help="수집일(YYYY-MM-DD). 명세에 기록한다")
    parser.add_argument("--refresh", action="store_true", help="저장된 원본이 있어도 다시 받는다")
    args = parser.parse_args()

    client = Client()
    raw_dir = HERE / "raw" / "kcmf"
    raw_dir.mkdir(parents=True, exist_ok=True)
    listing = client.get(LIST_URL).decode("utf-8", "replace")
    post_ids = list(dict.fromkeys(POST_ID.findall(listing)))
    if not post_ids:
        raise CollectError("목록에서 게시물을 찾지 못했다")

    entries = []
    for post_id in post_ids:
        entry = post_entry(client, post_id)
        path = download(client, entry, raw_dir, args.refresh)
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        entry["raw_path"] = path.relative_to(HERE).as_posix()
        entries.append(entry)
    years = [entry["year"] for entry in entries]
    if len(years) != len(set(years)):
        raise CollectError("같은 연도의 게시물이 둘 이상이다")

    manifest = {
        "publisher": "시청자미디어재단",
        "collection": "사전정보공표 '장애인방송 편성 실적(방송사명, 목표, 실적)'",
        "list_url": LIST_URL,
        "snapshot": args.snapshot.isoformat(),
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "access_note": "robots.txt는 모든 경로를 허용(2026-10-13 확인). 요청 사이 1초 간격, 원본 HWPX는 raw/에 두고 Git에서 제외",
        "files": sorted(entries, key=lambda item: item["year"]),
    }
    out = HERE / "data" / "kcmf_manifest.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(entries)}개 연도 수집: {min(years)}~{max(years)} → {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()

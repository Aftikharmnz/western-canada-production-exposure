"""Discover published regulator reports without baking a reporting year into URLs.

Only links actually present on the official report pages are accepted. Discovery
does not infer publication from the clock and does not read analyst workbooks.
The ETL owns binary downloads, immutable receipts, and fail-closed publication.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import datetime as dt
import re
import urllib.parse
import urllib.request

REPORT_PAGES = {
    "aer_st53": "https://www.aer.ca/data-and-performance-reports/statistical-reports/st53",
    "aer_st39": "https://www.aer.ca/data-and-performance-reports/statistical-reports/st39",
    "aer_st44": "https://www.aer.ca/data-and-performance-reports/statistical-reports/st44",
    "manitoba_well_production": "https://www.gov.mb.ca/iem/petroleum/reports/index.html",
}


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            values = dict(attrs)
            if values.get("href"):
                self.links.append(values["href"])


def _official_links(source_id: str, html: str) -> list[str]:
    parser = _Links()
    parser.feed(html)
    allowed_hosts = {"www.aer.ca", "aer.ca", "static.aer.ca"} if source_id.startswith("aer_") else {"www.gov.mb.ca", "gov.mb.ca"}
    result = set()
    for href in parser.links:
        url = urllib.parse.urljoin(REPORT_PAGES[source_id], href)
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in {"https", "http"} or parsed.hostname not in allowed_hosts or parsed.username or parsed.password:
            continue
        # The official sites support HTTPS; never follow a downgraded link.
        result.add(urllib.parse.urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, "")))
    return sorted(result)


def discover_report(source_id: str, html: str, history_start: str | None = None) -> list[dict]:
    """Parse one index page. Missing/ambiguous required links are errors."""
    if source_id not in REPORT_PAGES:
        raise ValueError(f"Unsupported report: {source_id}")
    if history_start is not None and not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", history_start):
        raise ValueError("history_start must be YYYY-MM")
    start_year = int(history_start[:4]) if history_start else 2017
    found = {}
    for url in _official_links(source_id, html):
        filename = Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path)).name
        info = None
        if source_id in {"aer_st53", "aer_st39"}:
            report = source_id.removeprefix("aer_")
            if re.fullmatch(rf"{report}(?:_Current)?\.xls[x]?", filename, re.I):
                extension = Path(filename).suffix.lower()
                info = {"current": True, "raw_file": f"{source_id}_current{extension}"}
            else:
                match = re.fullmatch(rf"{report}[-_](20\d{{2}})(?:[-_]12)?\.(xlsx?)", filename, re.I)
                if match and int(match[1]) >= start_year:
                    info = {"current": False, "report_year": int(match[1]), "raw_file": f"{source_id}_{match[1]}.{match[2].lower()}"}
        elif source_id == "aer_st44":
            match = re.fullmatch(r"ST44[-_](20\d{2})[-_]Q([1-4])\.(xlsx?)", filename, re.I)
            if match:
                info = {"current": True, "publication_period": f"{match[1]}-Q{match[2]}", "raw_file": f"aer_st44_current.{match[3].lower()}"}
        else:
            match = re.fullmatch(r"wmp[_-](\d{4})[_-](\d{4})[_-]excel\.zip", filename, re.I)
            if match and int(match[1]) <= int(match[2]) and (history_start is None or int(match[2]) >= start_year):
                info = {"start_year": int(match[1]), "end_year": int(match[2]), "raw_file": f"manitoba/{filename.lower()}"}
        if info:
            info.update(source_id=source_id, url=url, discovery_url=REPORT_PAGES[source_id])
            key = info.get("publication_period") or info["raw_file"]
            if key in found and found[key]["url"] != url:
                # Different official hostname/path aliases are common. Require
                # identical basename; otherwise the publication is ambiguous.
                old_name = Path(urllib.parse.urlsplit(found[key]["url"]).path).name.lower()
                if old_name != filename.lower():
                    raise ValueError(f"Ambiguous {source_id} publication: {key}")
            found[key] = info
    reports = list(found.values())
    if source_id in {"aer_st53", "aer_st39"}:
        if sum(bool(item.get("current")) for item in reports) != 1:
            raise ValueError(f"Official {source_id} page must have exactly one current XLS/XLSX link")
        reports.sort(key=lambda item: (item["current"], item.get("report_year", 9999)))
    elif source_id == "aer_st44":
        reports = sorted(reports, key=lambda item: item["publication_period"])[-1:]
    elif history_start is None:
        reports = sorted(reports, key=lambda item: (item["end_year"], item["start_year"]))[-1:]
    else:
        reports.sort(key=lambda item: (item["start_year"], item["end_year"]))
    if not reports:
        raise ValueError(f"Official {source_id} page contains no recognized published reports")
    return reports


def discover_sources(raw_dir: Path, history_start: str | None = None, timeout: int = 60,
                     source_ids: set[str] | None = None) -> list[dict]:
    """Fetch indexes, return descriptors, and cache the pages for an audit trail.

    Binary reports are not downloaded here. The caller must treat discovery
    failure as a failed refresh, not as evidence that a source disappeared.
    """
    if source_ids is not None and not source_ids.issubset(REPORT_PAGES):
        raise ValueError(f"Unsupported discovery sources: {source_ids - REPORT_PAGES.keys()}")
    descriptors = []
    for source_id, url in REPORT_PAGES.items():
        if source_ids is not None and source_id not in source_ids:
            continue
        request = urllib.request.Request(url, headers={"User-Agent": "ProductionLocations/1.0 (official public data refresh)"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.geturl().split("/", 3)[2] not in {"www.aer.ca", "aer.ca", "static.aer.ca", "www.gov.mb.ca", "gov.mb.ca"}:
                raise ValueError(f"Unexpected discovery redirect for {source_id}")
            body = response.read(5_000_001)
            if len(body) > 5_000_000:
                raise ValueError(f"Oversized discovery page for {source_id}")
            html = body.decode("utf-8", errors="strict")
        descriptors.extend(discover_report(source_id, html, history_start))
        target = Path(raw_dir) / "discovery" / f"{source_id}.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.with_suffix(".tmp").write_text(html, encoding="utf-8")
        target.with_suffix(".tmp").replace(target)
    return descriptors


def discover_aer_files(raw_dir: Path, source_id: str) -> list[Path]:
    """Cached annual publications first; the mutable current publication last."""
    if source_id not in {"aer_st53", "aer_st39"}:
        raise ValueError(f"Unsupported AER production report: {source_id}")
    pattern = re.compile(rf"{source_id}_(?:20\d{{2}}|current)\.xlsx?$")
    return sorted((path for path in Path(raw_dir).glob(f"{source_id}_*.xls*") if pattern.fullmatch(path.name)),
                  key=lambda path: ("_current." in path.name, path.name))


class _PetrinexRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.in_timestamp = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "tr" and values.get("data-file-type", "").startswith("Vol_"):
            if self.row is not None:
                raise ValueError("Nested Petrinex publication rows")
            self.row = {"file": values["data-file-type"], "checkbox": False, "timestamp": "", "filename": None, "category": None}
        if self.row is None:
            return
        if tag == "td":
            self.in_timestamp = values.get("data-col-type") == "Timestamp"
        if tag == "input":
            if values.get("type") == "checkbox" and values.get("data-control-element") == self.row["file"]:
                self.row["checkbox"] = "disabled" not in values
            if values.get("name", "").endswith(".FileName"):
                self.row["filename"] = values.get("value")
            if values.get("name", "").endswith(".FileCategory"):
                self.row["category"] = values.get("value")

    def handle_data(self, data):
        if self.row is not None and self.in_timestamp:
            self.row["timestamp"] += data

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_timestamp = False
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def parse_petrinex_months(jurisdiction: str, html: str) -> list[dict]:
    """Read enabled official Vol downloads and their revision timestamps.

    ``updated_at`` retains the regulator's timestamp without inventing a time
    zone. It is a revision token, not an observed UTC instant.
    """
    if jurisdiction not in {"AB", "SK"}:
        raise ValueError("Only verified Petrinex AB/SK publication indexes are supported")
    parser = _PetrinexRows()
    parser.feed(html)
    if parser.row is not None:
        raise ValueError("Truncated Petrinex publication index")
    rows = {}
    for item in parser.rows:
        match = re.fullmatch(r"Vol_(20\d{2}-(?:0[1-9]|1[0-2]))-(AB|SK)", item["file"])
        if not match or match[2] != jurisdiction:
            raise ValueError("Petrinex publication jurisdiction/period mismatch")
        if not item["checkbox"]:
            continue
        if item["filename"] != item["file"] or item["category"] != "Volumetric":
            raise ValueError("Petrinex volumetric file metadata changed")
        timestamp = item["timestamp"].strip()
        try:
            dt.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError("Missing/invalid Petrinex publication timestamp") from exc
        period = match[1]
        row = {"period": period, "updated_at": timestamp, "timestamp_timezone": "not specified by source",
               "url": f"https://www.petrinex.gov.ab.ca/publicdata/API/Files/{jurisdiction}/Vol/{period}/CSV"}
        if period in rows and rows[period] != row:
            raise ValueError("Conflicting Petrinex publication revisions")
        rows[period] = row
    if not rows:
        raise ValueError("Petrinex index contains no available volumetric publications")
    return [rows[period] for period in sorted(rows)]


def discover_petrinex_months(jurisdiction: str, raw_dir: Path, timeout: int = 60) -> list[dict]:
    """Discover real publications; an exception page is never an empty month list."""
    if jurisdiction not in {"AB", "SK"}:
        raise ValueError("Unsupported Petrinex jurisdiction")
    url = f"https://www.petrinex.gov.ab.ca/PublicData?Jurisdiction={jurisdiction}"
    request = urllib.request.Request(url, headers={"User-Agent": "western-canada-production-etl/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        resolved = urllib.parse.urlsplit(response.geturl())
        if resolved.scheme != "https" or resolved.hostname != "www.petrinex.gov.ab.ca" or "exception" in resolved.path.lower():
            raise ValueError("Petrinex publication index redirected to an unavailable page")
        body = response.read(5_000_001)
        if len(body) > 5_000_000:
            raise ValueError("Oversized Petrinex publication index")
        html = body.decode("utf-8", errors="strict")
    rows = parse_petrinex_months(jurisdiction, html)
    target = Path(raw_dir) / "discovery" / f"petrinex_{jurisdiction}.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(html, encoding="utf-8")
    temporary.replace(target)
    return rows

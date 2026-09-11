"""Monitor official refinery/tariff publications and import EIA crude capacities.

Writes reference_source_status.json and a separate eia_refinery_capacity.json.
Never changes reviewed tariffs, IIR geometry/units, or review verification dates.
Exit 0 means a monitoring report was written; --strict returns 2 if any source
failed or needs review. Neither mode sends notifications or requires private data.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
import math
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 40 * 1024 * 1024
EIA_HEADERS = ("CORPORATION", "SURVEY", "PERIOD", "COMPANY_NAME", "RDIST_LABEL", "STATE_NAME", "SITE", "PADD", "PRODUCT", "SUPPLY", "QUANTITY")
CAPACITY_PRODUCTS = {"OPERATING CAPACITY": "operating", "IDLE CAPACITY": "idle", "TOTAL OPERABLE CAPACITY": "operable"}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_bytes(url):
    if urllib.parse.urlsplit(url).scheme != "https":
        raise ValueError("Reference sources must use HTTPS")
    request = urllib.request.Request(url, headers={
        "User-Agent": os.environ.get("REFERENCE_USER_AGENT", "WCPEReferenceMonitor/1.0 (public energy data research)"),
        "Accept": "*/*",
    })
    with urllib.request.urlopen(request, timeout=40) as response:
        if urllib.parse.urlsplit(response.geturl()).scheme != "https":
            raise ValueError("Reference source redirected away from HTTPS")
        data = response.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Reference source is empty or exceeds the download limit")
    return data


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.text, self.hidden = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.text.append(data.strip())


def parse_page(payload):
    page = Page()
    page.feed(payload.decode("utf-8", errors="replace"))
    text = " ".join(" ".join(page.text).split())
    if len(text) < 80 or any(s in text[:800].lower() for s in ("access denied", "request blocked", "verify you are human", "just a moment")):
        raise ValueError("Reference page is empty or a service/access error")
    return page, text


def fingerprint(source, payload):
    kind = source["kind"]
    details = {}
    if kind == "pdf":
        if not payload.lstrip().startswith(b"%PDF-"):
            raise ValueError("Expected PDF, received a different document")
        normalized = payload
    elif kind == "sec_filings":
        data = json.loads(payload)
        recent = data.get("filings", {}).get("recent", {})
        names = ("form", "accessionNumber", "filingDate", "primaryDocument")
        if not all(isinstance(recent.get(k), list) for k in names) or len({len(recent[k]) for k in names}) != 1:
            raise ValueError("Invalid SEC filings response")
        rows = [dict(zip(names, values)) for values in zip(*(recent[k] for k in names)) if values[0] in {"10-Q", "10-K", "8-K", "10-Q/A", "10-K/A"}][:30]
        if not rows:
            raise ValueError("No recent refinery operator filings found")
        details["recent_filings"] = rows
        normalized = json.dumps(rows, sort_keys=True).encode()
    else:
        page, text = parse_page(payload)
        if kind == "pdf_index":
            links = sorted({urllib.parse.urldefrag(urllib.parse.urljoin(source["url"], link))[0] for link in page.links
                            if urllib.parse.urlsplit(link).path.lower().endswith(".pdf") and re.search(source.get("link_pattern", "."), link, re.I)})
            if not links:
                raise ValueError("No tariff PDF links found; publication index may have changed format")
            details["document_links"] = links
            normalized = "\n".join(links).encode()
        elif kind == "html":
            normalized = text.encode()
        else:
            raise ValueError(f"Unknown reference source kind: {kind}")
    return hashlib.sha256(normalized).hexdigest(), details


def check_source(source, previous=None, fetcher=fetch_bytes):
    previous = previous or {}
    result = {k: source[k] for k in ("id", "name", "kind", "url")}
    result["facts_last_verified"] = source.get("facts_last_verified")
    result["facts_automatically_updated"] = False
    try:
        digest, details = fingerprint(source, fetcher(source["url"]))
        result.update(available=True, fingerprint=digest, **details)
        reviewed = source.get("reviewed_sha256")
        # A change stays pending across repeated runs until its facts are reviewed.
        baseline = reviewed or previous.get("observation_baseline") or previous.get("fingerprint")
        result["comparison_basis"] = "reviewed_document" if reviewed else "observed_source" if baseline else "first_observation"
        result["observation_baseline"] = baseline or digest
        changed = baseline is not None and digest != baseline
        missing_review = source["kind"] == "pdf" and source["id"].startswith("tariff:") and not reviewed
        result["review_required"] = changed or missing_review
        result["status"] = "review_required" if result["review_required"] else "unchanged" if baseline else "available"
        if changed:
            result["reason"] = "Source fingerprint differs from its baseline; published facts have been preserved."
        elif missing_review:
            result["reason"] = "No reviewed PDF fingerprint is recorded; availability does not verify the rates."
        elif not reviewed:
            result["reason"] = "Availability/change monitoring only; source facts are not automatically re-verified."
    except Exception as exc:
        result.update(available=False, status="unavailable", review_required=True, error=str(exc))
        # Keep the baseline through failures so a later changed source is detected.
        for key in ("observation_baseline", "fingerprint", "document_links", "recent_filings"):
            if key in previous:
                result[key] = previous[key]
    return result


def discover_eia_workbook(payload, index_url):
    page, text = parse_page(payload)
    match = re.search(r"(?:With\s+)?Data for January\s+1,?\s+(20\d{2})", text, re.I)
    if not match:
        raise ValueError("EIA refinery survey date is not identified")
    year = int(match.group(1))
    links = {urllib.parse.urljoin(index_url, link) for link in page.links
             if re.search(rf"/refcap{str(year)[-2:]}\.xlsx$", urllib.parse.urlsplit(urllib.parse.urljoin(index_url, link)).path, re.I)}
    if len(links) != 1:
        raise ValueError("EIA current individual-refinery workbook is missing or ambiguous")
    url = links.pop()
    if urllib.parse.urlsplit(url).hostname != "www.eia.gov" or urllib.parse.urlsplit(url).scheme != "https":
        raise ValueError("Unexpected EIA workbook host")
    return year, url


def parse_eia_rows(rows, year):
    iterator = iter(rows)
    if tuple(next(iterator, ())) != EIA_HEADERS:
        raise ValueError("EIA refinery workbook column schema changed")
    facilities, observations, seen = {}, 0, set()
    for raw in iterator:
        if not any(value is not None for value in raw):
            continue
        if len(raw) != len(EIA_HEADERS):
            raise ValueError("EIA refinery row has an unexpected width")
        row = dict(zip(EIA_HEADERS, raw))
        if str(row["SURVEY"]) != "820" or str(row["PERIOD"]) not in {str(year), str(year)[-2:]}:
            raise ValueError("EIA survey or observation year mismatch")
        observations += 1
        supply, product = str(row["SUPPLY"]), row["PRODUCT"]
        if not supply.startswith("Atmospheric Crude Distillation Capacity") or product not in CAPACITY_PRODUCTS:
            continue  # Future-year projections and secondary units are not crude input.
        day = "calendar" if supply == "Atmospheric Crude Distillation Capacity (barrels per calendar day)" else "stream" if supply == "Atmospheric Crude Distillation Capacity (barrels per stream day)" else None
        if not day:
            raise ValueError("Unexpected EIA atmospheric capacity unit")
        identity = tuple(str(row[k] or "").strip() for k in ("COMPANY_NAME", "STATE_NAME", "SITE"))
        if not all(identity):
            raise ValueError("EIA facility identity is incomplete")
        key = (*identity, day, product)
        if key in seen:
            raise ValueError("Duplicate EIA facility capacity observation")
        seen.add(key)
        value = row["QUANTITY"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid EIA capacity; missing values cannot become zero")
        facility = facilities.setdefault(identity, {"company": identity[0], "state": identity[1], "site": identity[2], "corporation": row["CORPORATION"], "padd": str(row["PADD"]), "capacity_bbl_calendar_d": {}, "capacity_bbl_stream_d": {}})
        facility[f"capacity_bbl_{day}_d"][CAPACITY_PRODUCTS[product]] = value
    if not facilities:
        raise ValueError("EIA workbook has no atmospheric crude capacity records")
    for facility in facilities.values():
        for day in ("calendar", "stream"):
            capacity = facility[f"capacity_bbl_{day}_d"]
            if "operable" not in capacity or not ({"operating", "idle"} & capacity.keys()):
                raise ValueError("Incomplete EIA capacity breakdown")
            # EIA omits zero component rows. Infer zero only after the explicitly
            # reported total reconciles to the available component(s).
            if abs(sum(capacity.get(k, 0) for k in ("operating", "idle")) - capacity["operable"]) > 0.01:
                raise ValueError("EIA operating + idle capacity does not reconcile")
            capacity.setdefault("operating", 0)
            capacity.setdefault("idle", 0)
        capacity = facility["capacity_bbl_calendar_d"]
        facility["status_as_of_survey"] = "idle" if capacity["idle"] and not capacity["operating"] else "operating_with_idle_capacity" if capacity["idle"] else "operating"
    return {"as_of": f"{year}-01-01", "source_observation_count": observations,
            "facility_count": len(facilities), "facilities": [facilities[k] for k in sorted(facilities)]}


def archive_eia(payload, url, raw_dir):
    digest = hashlib.sha256(payload).hexdigest()
    path = raw_dir / f"{Path(urllib.parse.urlsplit(url).path).stem}-{digest}.xlsx"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temporary = path.with_suffix(".xlsx.tmp")
        temporary.write_bytes(payload)
        temporary.replace(path)
    elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("Archived EIA source hash mismatch")
    try:
        relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        relative = path.name
    receipt_path = path.with_suffix(".receipt.json")
    if not receipt_path.exists():
        atomic_json(receipt_path, dict(url=url, sha256=digest, bytes=len(payload), retrieved_at=utc_now(), raw_path=relative))
    return dict(raw_path=relative, raw_receipt=relative.removesuffix(".xlsx") + ".receipt.json", source_bytes=len(payload))


def fetch_eia(index_url, previous=None, fetcher=fetch_bytes, raw_dir=None):
    from openpyxl import load_workbook
    year, url = discover_eia_workbook(fetcher(index_url), index_url)
    if year > datetime.now(timezone.utc).year or (previous and f"{year}-01-01" < previous.get("as_of", "")):
        raise ValueError("EIA survey is future-dated or older than the published snapshot")
    payload = fetcher(url)
    if not payload.startswith(b"PK"):
        raise ValueError("EIA download is not an XLSX workbook")
    workbook = load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
    try:
        if len(workbook.worksheets) != 1:
            raise ValueError("EIA workbook sheet schema changed")
        result = parse_eia_rows(workbook.worksheets[0].iter_rows(values_only=True), year)
    finally:
        workbook.close()
    result.update(schema_version=1, source_url=url, source_index_url=index_url,
                  source_sha256=hashlib.sha256(payload).hexdigest(), retrieved_at=utc_now(),
                  scope="Facilities with reported atmospheric crude distillation capacity. This is not the count of all operable petroleum processing facilities; downstream-only plants are omitted.",
                  mapping_status="Independent EIA survey; not automatically joined to IIR geometry or later operating-status reviews.")
    if raw_dir is not None:
        result.update(archive_eia(payload, url, raw_dir))
    return result


def load_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def configured_sources(config, tariffs, refinery_review):
    sources = list(config["publication_indexes"])
    for key, doc in tariffs["documents"].items():
        sources.append(dict(id="tariff:" + key, name=doc["document_name"], kind="pdf", url=doc["url"],
                            reviewed_sha256=doc.get("sha256"), facts_last_verified=doc.get("last_verified", tariffs["metadata"]["last_verified"])))
    operators = {}
    for item in refinery_review.get("overrides", []) + refinery_review.get("status_overrides", []):
        url = urllib.parse.urldefrag(item["source_url"])[0]
        operators[url] = dict(id="refinery:" + hashlib.sha256(url.encode()).hexdigest()[:12], name=item["source_name"],
                              kind="pdf" if urllib.parse.urlsplit(url).path.lower().endswith(".pdf") else "html",
                              url=url, facts_last_verified=refinery_review["checked_at"])
    sources.extend(operators.values())
    for source in sources:
        reviewed_fingerprint = config.get("reviewed_fingerprints", {}).get(source["id"])
        if reviewed_fingerprint:
            if not re.fullmatch(r"[0-9a-f]{64}", reviewed_fingerprint):
                raise ValueError(f"Invalid reviewed fingerprint: {source['id']}")
            source["reviewed_sha256"] = reviewed_fingerprint
    if len({s["id"] for s in sources}) != len(sources):
        raise ValueError("Duplicate reference monitor IDs")
    return sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "data/reference_source_monitors.json")
    parser.add_argument("--output", type=Path, default=ROOT / "public/data/reference_source_status.json")
    parser.add_argument("--eia-output", type=Path, default=ROOT / "public/data/eia_refinery_capacity.json")
    parser.add_argument("--baseline", type=Path, help="Previous published reference report; defaults to --output")
    parser.add_argument("--eia-baseline", type=Path, help="Previous EIA snapshot; defaults beside --baseline, or to --eia-output")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/reference", help="Content-addressed EIA source archive with SHA256 receipts")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    config = load_json(args.config)
    tariffs = load_json(ROOT / "public/data/market_access_tariffs.json")
    review = load_json(ROOT / "data/refinery_capacity_overrides.json")
    previous = {r["id"]: r for r in (load_json(args.baseline or args.output, {}).get("checks") or [])}
    sources = configured_sources(config, tariffs, review)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        checks = list(pool.map(lambda source: check_source(source, previous.get(source["id"])), sources))
    eia = {"id": "eia_refinery_capacity", "name": "EIA annual refinery crude capacity", "url": config["eia_index_url"], "checked_at": utc_now()}
    eia_baseline = args.eia_baseline or (args.baseline.with_name("eia_refinery_capacity.json") if args.baseline else args.eia_output)
    prior = {}
    try:
        prior = load_json(eia_baseline, {})
        snapshot = fetch_eia(config["eia_index_url"], prior, raw_dir=args.raw_dir)
        changed = prior.get("source_sha256") != snapshot["source_sha256"]
        if changed:
            atomic_json(args.eia_output, snapshot)
        elif args.eia_output.resolve() != eia_baseline.resolve():
            atomic_json(args.eia_output, prior)
        eia.update(available=True, status="updated" if changed else "unchanged", review_required=changed,
                   facts_automatically_updated=changed, as_of=snapshot["as_of"], facility_count=snapshot["facility_count"],
                   source_url=snapshot["source_url"], raw_path=snapshot.get("raw_path"), raw_receipt=snapshot.get("raw_receipt"),
                   sha256=snapshot["source_sha256"], bytes=snapshot.get("source_bytes"), content_changed=changed,
                   reason="Official annual observations imported separately; integration with map identities and later statuses requires review.")
    except Exception as exc:
        if prior and args.eia_output.resolve() != eia_baseline.resolve():
            atomic_json(args.eia_output, prior)
        eia.update(available=False, status="unavailable", review_required=True, error=str(exc), preserved_previous_snapshot=bool(prior))
    checks.append(eia)
    next_change = tariffs["metadata"].get("next_known_change")
    due = bool(next_change and utc_now()[:10] >= next_change)
    if due:
        checks.append(dict(id="tariff_effective_date", name="Scheduled tariff change", status="review_required", review_required=True,
                           effective_date=next_change, reason="A known replacement effective date has arrived; current published rates remain on their original verification date."))
    report = dict(schema_version=1, checked_at=utc_now(), status="review_required" if any(c["review_required"] for c in checks) else "ok",
                  checks=checks, tariffs_last_verified=tariffs["metadata"]["last_verified"], refinery_facts_last_verified=review["checked_at"],
                  next_known_tariff_change=next_change, limitations=config["limitations"],
                  review_required_count=sum(c["review_required"] for c in checks),
                  failure_count=sum(c.get("available") is False for c in checks),
                  failures=[c["id"] for c in checks if c.get("available") is False])
    atomic_json(args.output, report)
    print(json.dumps({"status": report["status"], "checks": len(checks), "unavailable": sum(c.get("available") is False for c in checks),
                      "review_required": sum(c["review_required"] for c in checks), "tariffs_last_verified": report["tariffs_last_verified"]}))
    return 2 if args.strict and report["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

try:
    from convert_entries import REPORT_NAME, TABLE_NAME, convert_entries
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent))
    from convert_entries import REPORT_NAME, TABLE_NAME, convert_entries

# Constants
WIKI = "zh_min_nanwiktionary"
DUMPS_BASE = f"https://dumps.wikimedia.org/{WIKI}"
DUMP_FILE_TEMPLATE = WIKI + "-{date}-pages-articles.xml.bz2"
LATEST_DUMP_URL = f"{DUMPS_BASE}/latest/{DUMP_FILE_TEMPLATE.format(date='latest')}"
# Sits beside the `latest` file and names the dated run it points at. Used to
# download the dated URL instead, so the manifest records something that
# still resolves after `latest/` has moved on.
LATEST_RSS_URL = LATEST_DUMP_URL + "-rss.xml"
DUMP_DATE_PATTERN = re.compile(re.escape(WIKI) + r"-(\d{8})-pages-articles\.xml\.bz2")
# A --dump file: dated, .xml.bz2 or plain .xml. Never `latest`: a run that
# cannot name its dated dump does not publish (see resolve_dump).
LOCAL_DUMP_PATTERN = re.compile(re.escape(WIKI) + r"-(\d{8})-pages-articles\.xml(?:\.bz2)?")
USER_AGENT = "ChhoeTaigi-WiktionaryTaioanoeDataMirror/1.0 (https://github.com/ChhoeTaigi)"

# The published table, CSV and JSON, is what change detection compares. The
# dump is rebuilt every month and its own hash changes whenever ANY page does
# — hashing the table means a new version appears only when the Taigi
# entries, or how this repo renders them, actually changed. The report is
# not compared: a report-only change goes live with the next table change.
CHANGE_KEYS = [f"bunji/{TABLE_NAME}.csv", f"bunji/{TABLE_NAME}.json"]

# A partial failure upstream — a dump whose format changed, a template
# renamed — shows up as a sharp drop in these counts against the last
# version. Losing more than MAX_COUNT_DROP of any refuses to publish, unless
# --force.
WATCHED_COUNTS = ["rows", "rows_poj_title", "rows_reading_title", "rows_HanLoTaibunPoj"]
MAX_COUNT_DROP = 0.05

DOWNLOAD_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5
# A 429/503 from dumps.wikimedia.org is retried after its Retry-After, up to this.
RETRY_AFTER_MAX_SECONDS = 300
HTTP_TIMEOUT = 120
# The dump's Last-Modified, kept beside it (`….bz2.last-modified`) so a
# version published from a kept download still records it.
LAST_MODIFIED_SUFFIX = ".last-modified"

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
MANIFEST_FILE = PUBLIC_DIR / "manifest.json"
# A failed run leaves its complete download here, for the next attempt to
# start from. Gitignored, like every public/temp_update_*.
FAILED_DIR = PUBLIC_DIR / "temp_update_failed"
README_FILE = BASE_DIR / "README.md"
INDEX_FILE = BASE_DIR / "index.md"


def verify_docs_in_sync():
    """README.md and index.md must be byte-identical — a rule in every sibling
    mirror. Checked before any network work so a drift is cheap to fix."""
    if not README_FILE.exists() or not INDEX_FILE.exists():
        print("ERROR: both README.md and index.md must exist.")
        return False
    if README_FILE.read_bytes() != INDEX_FILE.read_bytes():
        print("ERROR: README.md and index.md have drifted apart.")
        print("       They must stay byte-identical. Fix with:")
        print("           cp README.md index.md")
        return False
    return True


def reserve_timestamp_dir():
    """Creates and returns a new, empty version directory named by the current
    second. Creating it is the reservation: two runs in the same second (or a
    clock stepped back) can no longer pick the same name."""
    while True:
        path = PUBLIC_DIR / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        try:
            path.mkdir()
            return path
        except FileExistsError:
            time.sleep(1)


def _open(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=HTTP_TIMEOUT)


def _retry_wait(error, attempt):
    """Seconds before retry number attempt: the backoff, or as long as a 429 or
    503 asks in its Retry-After, within RETRY_AFTER_MAX_SECONDS."""
    wait = RETRY_BACKOFF_SECONDS * attempt
    retry_after = (getattr(error, "headers", None) or {}).get("Retry-After") or ""
    if retry_after.isdigit():
        wait = max(wait, min(int(retry_after), RETRY_AFTER_MAX_SECONDS))
    return wait


def resolve_dump():
    """Returns (url, dump_date) of the dated run `latest/` points at, or
    (None, None) when the RSS cannot be read in DOWNLOAD_RETRIES tries or
    names no dated file. There is no fallback to the `latest/` URL: a version
    built from it could not be traced to a dump run."""
    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            with _open(LATEST_RSS_URL) as r:
                m = DUMP_DATE_PATTERN.search(r.read().decode("utf-8", "replace"))
        except Exception as e:
            print(f"Warning: could not read {LATEST_RSS_URL} "
                  f"(attempt {attempt}/{DOWNLOAD_RETRIES}): {e}")
            if attempt < DOWNLOAD_RETRIES:
                time.sleep(_retry_wait(e, attempt))
            continue
        if m:
            date = m.group(1)
            return f"{DUMPS_BASE}/{date}/{DUMP_FILE_TEMPLATE.format(date=date)}", date
        break
    return None, None


def download(url, target_path):
    """Downloads url to target_path with retry. Returns Last-Modified or None.

    Writes to a .part file renamed on success, so a failed download never
    looks complete, and checks the size against Content-Length: urllib hands
    back a body the server cut short as if it were whole."""
    part = target_path.with_name(target_path.name + ".part")
    last_error = None
    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            print(f"Downloading {url} (attempt {attempt}/{DOWNLOAD_RETRIES})...")
            with _open(url) as r, open(part, "wb") as out:
                shutil.copyfileobj(r, out)
                expected = r.getheader("Content-Length") or ""
                last_modified = r.getheader("Last-Modified")
            size = part.stat().st_size
            if expected.isdigit() and size != int(expected):
                raise OSError(f"got {size:,} of {int(expected):,} bytes")
            os.replace(part, target_path)
            return last_modified
        except Exception as e:
            last_error = e
            print(f"Error downloading {url}: {e}")
            if attempt < DOWNLOAD_RETRIES:
                time.sleep(_retry_wait(e, attempt))
    part.unlink(missing_ok=True)
    raise RuntimeError(f"Giving up on {url} after {DOWNLOAD_RETRIES} attempts: {last_error}")


def link_or_copy(source, target):
    """Hard-links source to target, or copies it across file systems. The
    dump is never written to, so sharing it costs no disk space."""
    try:
        os.link(source, target)
    except OSError:
        part = target.with_name(target.name + ".part")
        shutil.copy2(source, part)
        os.replace(part, target)


def failed_report_dir(dump_date):
    """Where a failed run of dump_date keeps the report it built: named by
    the dump run, so another run's report is neither replaced nor removed."""
    return FAILED_DIR / f"report-{dump_date or 'unknown'}"


def keep_for_resume(temp_dir, dump_date):
    """After a failed run, moves the complete download in temp_dir into
    FAILED_DIR, over a same-named file. The report the run built, if any,
    goes to FAILED_DIR/report-{dump_date}/, replacing an older one for the
    same dump run: a refused run is judged by it. Returns (names of the
    files kept, whether a report was kept)."""
    keep = sorted(p for p in temp_dir.iterdir()
                  if p.is_file() and not p.name.endswith(".part"))
    built = sorted((temp_dir / "version").glob(f"{REPORT_NAME}.*"))
    if keep or built:
        FAILED_DIR.mkdir(exist_ok=True)
    for path in keep:
        os.replace(path, FAILED_DIR / path.name)
    if built:
        report_dir = failed_report_dir(dump_date)
        shutil.rmtree(report_dir, ignore_errors=True)
        report_dir.mkdir()
        for path in built:
            os.replace(path, report_dir / path.name)
    return [path.name for path in keep], bool(built)


def clear_failed(dump_date):
    """After a successful run, removes what a failed run of the same dump run
    kept in FAILED_DIR — its download and its report: they are superseded.
    Another dump run's stay, for their own resume; FAILED_DIR goes once
    nothing is left in it."""
    if not FAILED_DIR.exists():
        return
    for path in FAILED_DIR.glob(f"{WIKI}-{dump_date}-*"):
        path.unlink()
    shutil.rmtree(failed_report_dir(dump_date), ignore_errors=True)
    if not any(FAILED_DIR.iterdir()):
        shutil.rmtree(FAILED_DIR)


def calculate_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def hash_published(version_dir):
    """{path relative to version_dir: sha256} for everything except tangloo/."""
    hashes = {}
    for path in sorted(version_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(version_dir)
        if rel.parts[0] == "tangloo":
            continue
        hashes[rel.as_posix()] = calculate_file_hash(path)
    return hashes


def load_manifest():
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_manifest(data):
    # Write to a temp file and atomically rename so a crash mid-write can't
    # leave a half-written manifest that breaks every subsequent run.
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_FILE.with_suffix(MANIFEST_FILE.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, MANIFEST_FILE)


def report_kept(kept, report, temp_dump, dump_date, refused):
    """Says what a failed run kept in FAILED_DIR and the command that starts
    from it."""
    if report:
        print(f"\nThe report this run built is in {failed_report_dir(dump_date)}"
              + (" — read it before rerunning with --force." if refused else "."))
    if not kept:
        return
    dumps = [n for n in kept if not n.endswith(LAST_MODIFIED_SUFFIX)]
    print(f"\nKept {len(dumps)} downloaded dump file(s) in {FAILED_DIR}.")
    if temp_dump is None or not (FAILED_DIR / temp_dump.name).exists():
        return
    command = f"python update_data.py --dump {FAILED_DIR / temp_dump.name}"
    if refused:
        command += " --force"
    print("Start from it with:")
    print(f"    {command}")


def main():
    parser = argparse.ArgumentParser(
        description="Mirror the Taigi entries of the zh-min-nan Wiktionary dump."
    )
    parser.add_argument(
        "--dump",
        metavar="PATH",
        help="Use a local pages-articles dump (.xml.bz2 or .xml) instead of "
             "downloading, as kept in every tangloo/ and in "
             "public/temp_update_failed/. It must keep its dated name.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Create a new version directory even when the table is "
             "unchanged, and publish even when counts fell sharply since the "
             "last version or the dump is older than the published one.",
    )
    args = parser.parse_args()
    # Titles and arrows must not crash a run on a terminal that is not UTF-8.
    sys.stdout.reconfigure(errors="backslashreplace")

    print("Starting update check...")

    if not verify_docs_in_sync():
        sys.exit(1)
    print("README.md and index.md are in sync.")

    current_manifest = load_manifest()
    latest_version_dir_name = current_manifest.get("latest_version_dir")

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="temp_update_", dir=str(PUBLIC_DIR)))

    target_dir = None
    temp_dump = None
    dump_date = None
    refused = False
    success = False
    try:
        # 1. Fetch the dump into temp (or take the local one).
        if args.dump:
            source = Path(args.dump).resolve()
            m = LOCAL_DUMP_PATTERN.fullmatch(source.name)
            if not m:
                # The manifest must name the dump each version was built from,
                # and only a dated filename identifies one.
                print(f"ERROR: {source.name} is not named "
                      f"{DUMP_FILE_TEMPLATE.format(date='YYYYMMDD')} (or without .bz2); "
                      "cannot record its source.")
                sys.exit(1)
            dump_date = m.group(1)
            dump_url = f"{DUMPS_BASE}/{dump_date}/{DUMP_FILE_TEMPLATE.format(date=dump_date)}"
            # Kept beside the dump by the run that downloaded it; else, for the
            # published version's own dump, the manifest's still holds.
            sidecar = source.with_name(source.name + LAST_MODIFIED_SUFFIX)
            if sidecar.is_file():
                last_modified = sidecar.read_text(encoding="utf-8").strip() or None
            elif current_manifest.get("source_dump") == dump_url:
                last_modified = current_manifest.get("source_dump_last_modified")
            else:
                last_modified = None
        else:
            dump_url, dump_date = resolve_dump()
            if dump_url is None:
                print(f"ERROR: could not tell from {LATEST_RSS_URL} which dated dump "
                      "run latest/ points at. Refusing to publish a version that "
                      "cannot be traced to one. Try again later.")
                sys.exit(1)
        # Publishing an older dump would quietly drop every entry added since.
        published_date = current_manifest.get("source_dump_date")
        if dump_date and published_date and dump_date < published_date and not args.force:
            print(f"ERROR: dump {dump_date} is older than {published_date}, which "
                  f"{latest_version_dir_name} was built from. Rerun with --force to "
                  "publish it anyway.")
            sys.exit(1)
        if args.dump:
            temp_dump = temp_dir / source.name
            link_or_copy(source, temp_dump)
            print(f"Using local dump: {source}")
        else:
            temp_dump = temp_dir / dump_url.rsplit("/", 1)[1]
            last_modified = download(dump_url, temp_dump)
            if last_modified:
                print(f"Source dump Last-Modified: {last_modified}")
        sidecar = temp_dir / (temp_dump.name + LAST_MODIFIED_SUFFIX)
        if last_modified:
            sidecar.write_text(last_modified + "\n", encoding="utf-8")
        downloaded = [temp_dump] + ([sidecar] if sidecar.exists() else [])

        # 2. Build into a staging version dir inside temp. Nothing under
        #    public/ is touched until conversion succeeded.
        staging = temp_dir / "version"
        stats = convert_entries(temp_dump, staging / "bunji", report_dir=staging)
        if stats["rows"] == 0:
            print("Kept 0 entries — refusing to publish an empty mirror. Aborting.")
            sys.exit(1)
        previous = current_manifest.get("counts", {})
        drops = [f"{key}: {previous[key]:,} → {stats.get(key, 0):,}"
                 for key in WATCHED_COUNTS
                 if previous.get(key) and stats.get(key, 0) < previous[key] * (1 - MAX_COUNT_DROP)]
        if drops and not args.force:
            print(f"Counts fell by more than {MAX_COUNT_DROP:.0%} since {latest_version_dir_name}:")
            for drop in drops:
                print(f"  {drop}")
            print("Refusing to publish. Rerun with --force if the drop is real.")
            refused = True
            sys.exit(1)

        new_hashes = hash_published(staging)
        cached_hashes = current_manifest.get("files", {})

        # 3. Change detection on the *published* table.
        existing_dir = PUBLIC_DIR / latest_version_dir_name if latest_version_dir_name else None
        changed = (args.force
                   or not cached_hashes
                   or any(new_hashes.get(k) != cached_hashes.get(k) for k in CHANGE_KEYS)
                   or existing_dir is None
                   or not existing_dir.exists())

        now = datetime.datetime.now().isoformat()
        if not changed:
            print(f"No changes in {', '.join(CHANGE_KEYS)}. Keeping {latest_version_dir_name}.")
            # Record that the mirror was checked against this dump.
            new_manifest = dict(current_manifest)
            new_manifest["last_checked"] = now
            # Never moved back (--force with an older dump).
            new_manifest["last_checked_dump_date"] = max(
                dump_date, current_manifest.get("last_checked_dump_date") or "")
            save_manifest(new_manifest)
            success = True
            target_dir = existing_dir
        else:
            print("Changes detected (or --force). Creating a new version directory...")
            target_dir = reserve_timestamp_dir()
            for item in staging.iterdir():
                shutil.move(str(item), str(target_dir / item.name))
            # tangloo/ keeps the downloaded dump beside the table it produced.
            # Gitignored: it is what was downloaded, not what this repo
            # publishes.
            tangloo = target_dir / "tangloo"
            tangloo.mkdir()
            for path in downloaded:
                shutil.move(str(path), str(tangloo / path.name))

            new_manifest = {
                "last_updated": now,
                "last_checked": now,
                # Never moved back: November checked, October republished.
                "last_checked_dump_date": max(
                    dump_date, current_manifest.get("last_checked_dump_date") or ""),
                "latest_version_dir": target_dir.name,
                "source_dump": dump_url,
                "source_dump_date": dump_date,
                "source_dump_last_modified": last_modified,
                "license": "CC-BY-SA-4.0",
                "row_count": stats["rows"],
                "files": new_hashes,
                "counts": stats,
            }
            save_manifest(new_manifest)
            # Published: from here on, a failure must not remove target_dir.
            success = True
            print(f"Created {target_dir} and updated manifest.json.")

        clear_failed(dump_date)
    finally:
        if not success and target_dir and target_dir.exists() \
                and target_dir.name != latest_version_dir_name:
            # Hand this run's download and report back to temp_dir first,
            # so they are kept for resume below.
            tangloo = target_dir / "tangloo"
            if tangloo.is_dir():
                for path in tangloo.iterdir():
                    os.replace(path, temp_dir / path.name)
            staging = temp_dir / "version"
            staging.mkdir(exist_ok=True)
            for path in target_dir.glob(f"{REPORT_NAME}.*"):
                os.replace(path, staging / path.name)
            print(f"Removing partial target directory: {target_dir}")
            shutil.rmtree(target_dir)
        if temp_dir.exists():
            if not success:
                report_kept(*keep_for_resume(temp_dir, dump_date), temp_dump, dump_date, refused)
            shutil.rmtree(temp_dir)

    print("\nUpdate complete!")
    if target_dir:
        print(f"Data stored in: {target_dir}")


if __name__ == "__main__":
    main()

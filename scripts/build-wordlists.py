#!/usr/bin/env python3
"""Build curated 4/5/6-letter playable lists ranked by wordfreq Zipf.

Dev-only. Runtime reads the committed JSON. See ATTRIBUTION.md.
"""

from __future__ import annotations

import csv
import json
import re
import ssl
import urllib.request
import zipfile
from pathlib import Path

import certifi
from wordfreq import top_n_list, zipf_frequency

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = ROOT / "src" / "data" / "words"
CACHE_DIR = SCRIPT_DIR / ".cache"
BLOCKLIST_PATH = SCRIPT_DIR / "blocklist-en.txt"
LDNOOBW_URL = (
    "https://raw.githubusercontent.com/LDNOOBW/"
    "List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master/en"
)

# SSA.gov names.zip 403s scripted clients. Prefer a local copy if you drop
# it in scripts/.cache/names.zip; otherwise a GitHub SSA mirror.
SSA_BOYS_URL = "https://raw.githubusercontent.com/dxdc/babynames/main/data/boys.csv"
SSA_GIRLS_URL = "https://raw.githubusercontent.com/dxdc/babynames/main/data/girls.csv"
WORDNET_ZIP_URL = (
    "https://raw.githubusercontent.com/nltk/nltk_data/"
    "gh-pages/packages/corpora/wordnet.zip"
)

UA = "caret-wordlists/1.0 (+https://caret.joris.wtf)"
WORD_RE = re.compile(r"^[a-z]{4,6}$")
ZIPF_FLOOR = 3.4
TOP_N = 100_000
SSA_RANK_LIMIT = 2000
SSA_MIN_COUNT = 5_000
SSA_YEAR_TOP = 1000

# Places WordNet encodes as a keepable type (royal house, plant genus)
# rather than a location instance.
EXTRA_PLACES = {"york", "paris"}

# When a place-name has another WordNet sense, ignore these lexnames so
# "people of Miami" or "ancient Greece" do not save the toponym.
PLACE_WEAK_LEX = {"noun.location", "noun.person", "noun.group"}

# Wordle answer rule for calendar names: APRIL is out, MARCH stays (verb).
# noun.time is the month/weekday/holiday itself; phenomenon catches Easter wind.
CALENDAR_WEAK_LEX = {
    "noun.time",
    "noun.person",
    "noun.location",
    "noun.group",
    "noun.phenomenon",
}
CALENDAR_ROOTS = (
    "gregorian_calendar_month.n.01",
    "day_of_the_week.n.01",
    "rest_day.n.01",
    "holiday.n.02",
    "religious_holiday.n.01",
    "movable_feast.n.01",
    "feast_day.n.01",
    "legal_holiday.n.01",
)

# Closed-class / function words that dominate short frequency lists.
FUNCTION_WORDS = {
    "that", "with", "have", "they", "from", "this", "what", "when", "your",
    "will", "would", "there", "their", "about", "which", "could", "other",
    "after", "first", "than", "then", "them", "these", "those", "into",
    "some", "more", "also", "just", "only", "over", "such", "even", "most",
    "many", "much", "very", "well", "back", "here", "where", "being",
    "been", "were", "does", "both", "each", "same", "upon", "unto", "whom",
    "whose", "while", "though", "should", "shall", "might", "under",
    "above", "again", "still", "never", "always", "often", "every",
    "myself", "itself", "yours", "ours", "hers", "his", "its", "our",
    "their", "theirs", "yourself", "because", "before", "between",
    "through", "during", "without", "within", "against", "among",
    "across", "around", "behind", "beside", "beyond", "except",
    "inside", "toward", "towards", "until", "whether", "either",
    "neither", "another", "anyone", "anybody", "anything", "everyone",
    "everybody", "everything", "someone", "somebody", "something",
    "nothing", "nobody", "nowhere", "everywhere", "somewhere",
    "whatever", "whoever", "whomever", "however", "therefore",
    "although", "unless", "since", "while", "where", "there",
    "hence", "thus", "quite", "rather", "almost", "already",
    "anyway", "anyway", "else", "ever", "less", "least", "able",
    "cannot", "could", "would", "should", "might", "must", "shall",
    "doing", "done", "having", "being",
}

# Tail junk that survives the Zipf floor: abbreviations, roman numerals,
# internet crumbs, crossword bait. Inspected from the rarest ~50 / length.
HAND_DROP = {
    "http", "https", "html", "json", "null", "true", "xhr", "www",
    "com", "org", "edu", "gov", "jpg", "png", "gif", "pdf", "css",
    "xml", "sql", "api", "url", "uri", "utf", "ascii", "iso",
    "viii", "xiii", "xiv", "xvii", "xviii", "xxii", "xxiii", "xxiv",
    "xxvi", "xxix", "xxxi", "xxxii", "xxxiv", "xxxix",
    "lol", "lmao", "lmfao", "omg", "wtf", "idk", "tbh", "imo", "imho",
    "aka", "etc", "ie", "eg", "vs", "ok", "okay", "yeah", "yep", "nope",
    "oops", "huh", "hmm", "nah", "yup", "wow", "hah", "haha", "hehe",
    "blah", "meh", "ugh", "dude", "bro", "sis",
    "cwm", "cwms", "crwth", "qoph", "qophs", "qat",
    "nth", "pfft", "psst", "shhh", "zzzz",
    "xxxx", "xxxxx", "xxxxxx", "aaaa", "aaaah",
    "doi", "issn", "isbn", "llc", "inc", "ltd",
    # Tail pass: names, brands, abbrevs, sexual/strong leftovers
    "cavs", "dirk", "elle", "elsa", "fran", "kemp", "trey", "vivo",
    "ames", "cary", "moto", "vega", "yong", "dora", "otis", "prob",
    "amir", "feng", "lars", "lori", "pepe", "pimp", "piss",
    "kyoto", "levin", "lgbtq", "moran", "starr", "wolfe", "alvin",
    "judah", "kabul", "paolo", "polly", "rosen", "rossi",
    "spacex", "stacey", "tobago", "anders", "darius", "felipe",
    "kelley", "malibu", "merkel", "patton", "sahara", "womens",
    "usda", "oecd", "dani", "burt", "cara", "barca", "conan",
    "duffy", "fedex", "quincy", "nasdaq", "marian", "mens",
}


def ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 2048:
        if dest.suffix == ".zip" and not zipfile.is_zipfile(dest):
            dest.unlink()
        else:
            return
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60, context=ssl_context()) as res:
        dest.write_bytes(res.read())
    if dest.suffix == ".zip" and not zipfile.is_zipfile(dest):
        dest.unlink(missing_ok=True)
        raise OSError(f"not a zip: {url}")


def ensure_wordnet():
    import nltk
    from nltk.corpus import wordnet as wordnet

    data_dir = CACHE_DIR / "nltk_data"
    nltk.data.path.insert(0, str(data_dir))
    probe = data_dir / "corpora" / "wordnet" / "index.noun"
    if not probe.exists():
        archive = CACHE_DIR / "wordnet.zip"
        fetch(WORDNET_ZIP_URL, archive)
        corpora = data_dir / "corpora"
        corpora.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(corpora)
    return wordnet


def names_from_ssa_zip(path: Path) -> set[str]:
    names: set[str] = set()
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            filename = Path(info.filename).name
            if not re.fullmatch(r"yob\d{4}\.txt", filename):
                continue
            counts = {"M": 0, "F": 0}
            with zf.open(info) as handle:
                for raw in handle:
                    line = raw.decode("utf-8").strip()
                    if not line:
                        continue
                    name, sex, _count = line.split(",")
                    if sex not in counts or counts[sex] >= SSA_YEAR_TOP:
                        continue
                    counts[sex] += 1
                    word = name.lower()
                    if WORD_RE.match(word):
                        names.add(word)
    return names


def names_from_ssa_csv(path: Path) -> set[str]:
    """All-time popular given names. Primary spellings only.

    The GitHub CSVs also list phonetic 'spelling_variants' (Juana → Wanna).
    Those over-group and would drop real words, so they are ignored.
    """
    names: set[str] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rank = int(row["rank"])
            count = int(row["total_count"])
            if rank > SSA_RANK_LIMIT and count < SSA_MIN_COUNT:
                continue
            word = re.sub(r"[^a-z]", "", row["name"].lower())
            if WORD_RE.match(word):
                names.add(word)
    return names


def load_given_names() -> set[str]:
    zip_path = CACHE_DIR / "names.zip"
    if zip_path.exists() and zipfile.is_zipfile(zip_path):
        names = names_from_ssa_zip(zip_path)
        print(f"given names: {len(names)} from SSA zip (top {SSA_YEAR_TOP}/sex/year)")
        return names
    boys = CACHE_DIR / "ssa-boys.csv"
    girls = CACHE_DIR / "ssa-girls.csv"
    fetch(SSA_BOYS_URL, boys)
    fetch(SSA_GIRLS_URL, girls)
    names = names_from_ssa_csv(boys) | names_from_ssa_csv(girls)
    print(
        f"given names: {len(names)} from SSA mirror "
        f"(rank ≤ {SSA_RANK_LIMIT} or count ≥ {SSA_MIN_COUNT})"
    )
    return names


def _hyponyms(syn) -> list:
    seen = set()
    stack = [syn]
    out = []
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        out.append(current)
        stack.extend(current.hyponyms())
    return out


def calendar_lemmas(wordnet) -> set[str]:
    """Month, weekday, and holiday names. Same proper-noun cut Wordle uses."""
    lemmas: set[str] = set()
    for name in CALENDAR_ROOTS:
        try:
            root = wordnet.synset(name)
        except LookupError:
            continue
        for syn in _hyponyms(root):
            for lemma in syn.lemma_names():
                token = lemma.lower()
                if "_" not in token and WORD_RE.match(token):
                    lemmas.add(token)
    return lemmas


def instance_lemmas(wordnet, lexname: str) -> set[str]:
    lemmas: set[str] = set()
    for syn in wordnet.all_synsets("n"):
        if syn.lexname() != lexname or not syn.instance_hypernyms():
            continue
        for lemma in syn.lemma_names():
            token = lemma.lower()
            if "_" not in token and WORD_RE.match(token):
                lemmas.add(token)
    return lemmas


def exact_synsets(wordnet, word: str):
    return [
        syn
        for syn in wordnet.synsets(word)
        if word in {lemma.name().lower() for lemma in syn.lemmas()}
    ]


def keepable_synsets(
    wordnet, word: str, weak_lex: set[str] | frozenset[str] | None = None
) -> bool:
    for syn in exact_synsets(wordnet, word):
        if syn.instance_hypernyms():
            continue
        if weak_lex and syn.lexname() in weak_lex:
            continue
        return True
    return False


def plausible_bases(wordnet, form: str) -> set[str]:
    """Inflection stems that are not NLTK's james→jam -es strip."""
    bases: set[str] = set()
    for pos in (wordnet.NOUN, wordnet.VERB, wordnet.ADJ):
        for lemma in wordnet._exception_map.get(pos, {}).get(form, []):
            if lemma != form:
                bases.add(lemma)
    if len(form) < 5 or not form.endswith("s") or form.endswith("ss"):
        return {base for base in bases if base}
    # mile→miles looks like -es but is +s; only strip -es after a sibilant.
    if form.endswith("ies") and form[-4] not in "aeiou":
        bases.add(form[:-3] + "y")
    elif form.endswith(("ches", "shes", "sses", "xes", "zes")):
        bases.add(form[:-2])
    else:
        bases.add(form[:-1])
    return {base for base in bases if base and base != form}


def is_proper_only(
    wordnet,
    word: str,
    names: set[str],
    places: set[str],
    people: set[str],
    calendar: set[str],
) -> bool:
    if word in EXTRA_PLACES:
        return True
    is_place = word in places
    is_calendar = word in calendar
    if word not in names and not is_place and word not in people and not is_calendar:
        return False
    if is_place:
        weak: set[str] | frozenset[str] | None = PLACE_WEAK_LEX
    elif is_calendar:
        weak = CALENDAR_WEAK_LEX
    else:
        weak = None
    if keepable_synsets(wordnet, word, weak):
        return False
    for base in plausible_bases(wordnet, word):
        if zipf_frequency(base, "en") < ZIPF_FLOOR:
            continue
        if keepable_synsets(wordnet, base):
            return False
    return True


def load_profanity() -> set[str]:
    if BLOCKLIST_PATH.exists():
        text = BLOCKLIST_PATH.read_text(encoding="utf-8")
    else:
        fetch(LDNOOBW_URL, BLOCKLIST_PATH)
        text = BLOCKLIST_PATH.read_text(encoding="utf-8")
    words = set()
    for line in text.splitlines():
        item = line.strip().lower()
        if not item or item.startswith("#"):
            continue
        words.add(re.sub(r"[^a-z]", "", item))
        words.add(item)
    return {w for w in words if w}


def is_playable(word: str, blocked: set[str]) -> bool:
    if not WORD_RE.match(word):
        return False
    if word in FUNCTION_WORDS or word in HAND_DROP or word in blocked:
        return False
    return True


def main() -> None:
    wordnet = ensure_wordnet()
    blocked = load_profanity()
    names = load_given_names()
    places = instance_lemmas(wordnet, "noun.location")
    people = instance_lemmas(wordnet, "noun.person")
    calendar = calendar_lemmas(wordnet)
    print(
        f"WordNet instances 4–6: {len(places)} places, {len(people)} people; "
        f"calendar: {len(calendar)}; extra places: {', '.join(sorted(EXTRA_PLACES))}"
    )

    buckets: dict[int, list[dict[str, float | str]]] = {4: [], 5: [], 6: []}
    seen = {4: set(), 5: set(), 6: set()}
    proper_drops: dict[int, list[str]] = {4: [], 5: [], 6: []}

    for word in top_n_list("en", TOP_N, wordlist="best"):
        word = word.lower()
        if not is_playable(word, blocked):
            continue
        z = zipf_frequency(word, "en")
        if z < ZIPF_FLOOR:
            continue
        n = len(word)
        if word in seen[n]:
            continue
        if is_proper_only(wordnet, word, names, places, people, calendar):
            proper_drops[n].append(word)
            continue
        seen[n].add(word)
        buckets[n].append({"w": word, "z": round(z, 2)})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    kept_words = {item["w"] for rows in buckets.values() for item in rows}
    sanity_keep = (
        "mark",
        "rose",
        "grace",
        "frank",
        "robin",
        "china",
        "japan",
        "miles",
        "march",
        "august",
    )
    sanity_drop = (
        "nicole",
        "paul",
        "sarah",
        "david",
        "james",
        "york",
        "paris",
        "april",
        "june",
        "july",
        "monday",
        "korea",
    )
    sanity_fail = [
        *[f"kept {w}" for w in sanity_drop if w in kept_words],
        *[f"dropped {w}" for w in sanity_keep if w not in kept_words],
    ]
    if sanity_fail:
        raise SystemExit("name filter sanity failed: " + ", ".join(sanity_fail))

    for n, rows in buckets.items():
        rows.sort(key=lambda item: (-float(item["z"]), str(item["w"])))
        path = OUT_DIR / f"{n}.json"
        path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        tail = ", ".join(str(item["w"]) for item in rows[-50:])
        dropped = proper_drops[n]
        print(
            f"{n}: {len(rows)} words  zipf "
            f"{rows[-1]['z'] if rows else '-'}–{rows[0]['z'] if rows else '-'}  "
            f"dropped {len(dropped)} names/places"
        )
        print(f"  dropped: {', '.join(dropped[:40])}{' …' if len(dropped) > 40 else ''}")
        print(f"  tail: {tail}")


if __name__ == "__main__":
    main()

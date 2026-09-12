#!/usr/bin/env python3
"""Build curated 4/5/6-letter playable lists ranked by wordfreq Zipf.

Dev-only. Runtime reads the committed JSON. See ATTRIBUTION.md.
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

from wordfreq import top_n_list, zipf_frequency

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "src" / "data" / "words"
BLOCKLIST_PATH = Path(__file__).resolve().parent / "blocklist-en.txt"
LDNOOBW_URL = (
    "https://raw.githubusercontent.com/LDNOOBW/"
    "List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master/en"
)

WORD_RE = re.compile(r"^[a-z]{4,6}$")
ZIPF_FLOOR = 3.4
TOP_N = 100_000

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

def load_profanity() -> set[str]:
    if BLOCKLIST_PATH.exists():
        text = BLOCKLIST_PATH.read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(LDNOOBW_URL, timeout=30) as res:
            text = res.read().decode("utf-8")
        BLOCKLIST_PATH.write_text(text, encoding="utf-8")
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
    blocked = load_profanity()
    buckets: dict[int, list[dict[str, float | str]]] = {4: [], 5: [], 6: []}
    seen = {4: set(), 5: set(), 6: set()}

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
        seen[n].add(word)
        buckets[n].append({"w": word, "z": round(z, 2)})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for n, rows in buckets.items():
        rows.sort(key=lambda item: (-float(item["z"]), str(item["w"])))
        path = OUT_DIR / f"{n}.json"
        path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        tail = ", ".join(str(item["w"]) for item in rows[-50:])
        print(f"{n}: {len(rows)} words  zipf {rows[-1]['z'] if rows else '-'}–{rows[0]['z'] if rows else '-'}")
        print(f"  tail: {tail}")


if __name__ == "__main__":
    main()

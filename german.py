#!/usr/bin/env python3
from collections import defaultdict
from os.path import exists
import re
import requests
from requests.exceptions import RequestException
from argparse import ArgumentParser
import tarfile

SOURCE = "https://pcai056.informatik.uni-leipzig.de"
wiki_1M_url = f"{SOURCE}/downloads/corpora/deu_wikipedia_2021_1M.tar.gz"
news_1M_url = f"{SOURCE}/downloads/corpora/deu_news_2021_1M.tar.gz"
FILE_NAME_PATTERN = "deu_{type}_{year}_{amount}.tar.gz"
URL_PATTERN = f"{SOURCE}/downloads/corpora/{{file_name}}"

LOWERCASE_WORDS = [
    "Ab", "Aber", "Alle", "Allein", "Allerdings", "Als", "Also", "Am", "An",
    "Andererseits", "Anschließend", "Ansonst", "Ansonsten", "Anstatt", "Auch",
    "Auf", "Aufgrund", "Ausgenommen", "Außer", "Außerdem", "Bei", "Beim",
    "Bereits", "Bevor", "Beziehungsweise", "Bis", "Bloß", "Da", "Dabei",
    "Dadurch", "Dafür", "Dagegen", "Daher", "Damit", "Danach", "Daneben",
    "Dann", "Darauf", "Darum", "Darüber", "Das", "Dass", "Davor", "Dazu",
    "Dem", "Den", "Denen", "Denn", "Dennoch", "Der", "Deren", "Derer", "Des",
    "Deshalb", "Dessen", "Desto", "Deswegen", "Die", "Dies", "Diese", "Diesem",
    "Diesen", "Dieser", "Dieses", "Doch", "Dort", "Durch", "Ebenso", "Ein",
    "Eine", "Einem", "Einen", "Einer", "Einerseits", "Eines", "Einige",
    "Entweder", "Er", "Erst", "Es", "Falls", "Ferner", "Folglich", "Für",
    "Genauso", "Geschweige", "Gleichwie", "Heute", "Hier", "Ich", "Ihm", "Ihn",
    "Im", "Immerhin", "In", "Indem", "Indes", "Indessen", "Insgesamt",
    "Insofern", "Insoweit", "Inzwischen", "Je", "Jedennoch", "Jedoch", "Jene",
    "Jenem", "Jenen", "Jener", "Jenes", "Kaum", "Man", "Minus", "Mit", "Nach",
    "Nachdem", "Neben", "Nicht", "Noch", "Nun", "Nur", "Nämlich", "Ob",
    "Obgleich", "Obschon", "Obwohl", "Obzwar", "Oder", "Ohne", "Plus",
    "Respektive", "Schließlich", "Schon", "Sein", "Seine", "Seit", "Seitdem",
    "Selbst", "So", "Sobald", "Sodass", "Sofern", "Sogar", "Solange", "Somit",
    "Sondern", "Sonst", "Sooft", "Sosehr", "Soviel", "Soweit", "Sowenig",
    "Sowie", "Sowohl", "Später", "Statt", "Trotz", "Trotzdem", "Um", "Umso",
    "Und", "Unter", "Ursprünglich", "Viele", "Vom", "Von", "Vor", "Vorher",
    "Wann", "Was", "Weder", "Wegen", "Weil", "Weitere", "Welche", "Welchem",
    "Welchen", "Welcher", "Welches", "Wem", "Wen", "Wenn", "Wenngleich",
    "Wennschon", "Wer", "Wessen", "Wie", "Wieweit", "Wiewohl", "Wo", "Wofern",
    "Wohingegen", "Während", "Währenddem", "Währenddessen", "Zu", "Zudem",
    "Zum", "Zumal", "Zur", "Zuvor", "Zwar", "Zwischen",
    # specials (opinionated)
    # "Aus",    # could be a nomen
    "Ihnen",    # could be capital
    "Ihr",      # could be capital
    "Ihre",     # could be capital
    "Ihrem",    # could be capital
    "Ihren",    # could be capital
    "Ihrer",    # could be capital
    "Ihres",    # could be capital
    "Sie",      # could be capital
]

# The following "non-german" words are quite opinionated
# These can be abbreviations (e.g. CDs), political parties, numerals or just
# not german at all.
NON_GERMAN_WORDS = [
    "AfD", "CDs", "MHz", "New", "StGB", "The", "UdSSR" "de", "La", "San",
    "School",
]


def download_file(url: str, file_name: str) -> None:
    """Download archive to current folder"""
    try:
        r = requests.get(url, stream=True)
    except RequestException as e:
        raise SystemExit(e)
    r.raise_for_status()

    with open(f"./{file_name}", "wb") as f:
        f.write(r.raw.read())


def words_from_file_in_archive(file_name: str, archive_name: str) -> dict:
    """Extract words file from archive and return it as dict

    The word will be the key, the value will be the frequency

    This assumes every line looks like this:
    rank<tab>word<tab>word frequency<newline>
    1	der	499367
    """
    words = defaultdict(int)
    with tarfile.open(archive_name, mode="r:gz") as tar:
        words_file = tar.extractfile(file_name)

        for line in words_file.readlines():
            line_list = line.decode("utf-8").strip().split("\t")
            words[line_list[1].strip()] += int(line_list[2])

    return words


def filter_words(words: dict) -> list:
    """Sanatize words dict in multiple ways and return list ordered by frquency

    - Remove everything not a german latter
      (exclamation points, kommas, foreign characters)
    - Remove one letter words, like "m" (wtf?)
    - Remove non german words
    - Remove abbreviations (words with only capital letters)
    - Remove words that only appeared once in the source material
    - Fix capitalisation, since some words are only uppercase because of their
      position at the start of a sentence
    """
    filtered_words = defaultdict(int)

    german_characters = re.compile("[^a-zA-ZäöüÄÖÜßẞ]")
    ABBREVIATION_REGEX = re.compile("^[A-ZÄÖÜẞ]+$")
    for word, frequency in words.items():
        # skip words with invalid "characters" like:
        # special characters or characters from another language
        if (
            re.search(german_characters, word)      # non german letter
            or len(word) == 1                       # one letter word
            or word in NON_GERMAN_WORDS             # non german words
            or re.search(ABBREVIATION_REGEX, word)  # abbreviations
            or frequency == 1                       # one time occurences
        ):
            continue

        # some words are only uppercase in the collection due to a new sentence
        # we treat them like they were lowercase
        if word in LOWERCASE_WORDS:
            word = word.lower()

        filtered_words[word] += frequency

    # TODO: implement verbose
    print(
        "Removed",
        len(words)-len(filtered_words),
        (len(words)-len(filtered_words))/len(words),
    )

    sorted_list = [
        word
        for word, _ in sorted(filtered_words.items(),
                              key=lambda x: x[1],
                              reverse=True)
    ]

    return sorted_list


def main(args):
    archive_name = FILE_NAME_PATTERN.format(
        type=args.type,
        amount=args.amount,
        year=args.year)
    url = URL_PATTERN.format(file_name=archive_name)

    if not exists(archive_name) or not tarfile.is_tarfile(archive_name):
        download_file(url, archive_name)

    # read directly from requests?
    # tar = tarfile.open(fileobj=r.raw, mode="r:gz")

    words = words_from_file_in_archive(
        (f"deu_{args.type}_{args.year}_{args.amount}/"
         f"deu_{args.type}_{args.year}_{args.amount}-words.txt"),
        archive_name
    )

    words = filter_words(words)

    # TODO: write files in correct format


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "type",
        choices=["wikipedia", "news"])
    parser.add_argument(
        "amount",
        choices=["10k", "30k", "100k", "300K", "1M"],
        nargs="?",
        default="1M")
    parser.add_argument(
        "amount",
        nargs="?",
        choices=["10k", "30k", "100k", "300K", "1M"],
        default="1M")
    parser.add_argument(
        "year",
        nargs="?",
        choices=["2021"],
        default="2021")
    args = parser.parse_args()

    main(args)

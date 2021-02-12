import sys
import signal
from contextlib import contextmanager
import os.path
import random
from datetime import datetime
import csv

from googlesearch import get_random_user_agent
from search_engines import *


ASYNC_REQUEST_LIMIT = 25
PAGE_LOAD_WAIT = 1
SUBJECT_XPATH = "//div[{}]/ul/li/a/text()"

search_engines = [
    Ask,
    Bing,
    Dogpile,
    Duckduckgo,
    Google,
    Mojeek,
    Startpage,
    Yahoo
]


def main():
    # open the county list csv
    with open('county_list.csv', newline='') as f:
        r = csv.reader(f, delimiter=',')
        # for each county/state tuple
        for row in r:
            county, state = row[0], row[1]
            print(county, state)
        # choose a random search engine

        # search for `site:gov <county> county <state> covid vaccine`
        # open the info file for the specified state and county
        # if the directory/file doesn't exist, add it
        # if the contents of the file is [whitespace]No tips submitted for this location yet.[whitespace] then truncate the file
        # append the link, link description, source (this scraper), and MLA citation to the file in md format
        # move to the next county


def build_codex(doc_count=1000, subjects_dir="research/data/arbitrary", destination_dir="research/data/arbitrary/codex"):
    # Number of documents to try to retrieve for each subject-batch.
    SUBJECT_BATCH_SIZE = 10
    # Number of pages of results to request per engine per batch.
    SEARCH_PAGES = 5
    ENGINE_COOLDOWN_TIME = 5

    engine_times = dict()

    def _search():
        time_since_last_use = 0
        prush("Selecting an engine...")
        engine_name = ""
        while True:
            engine = random.choice(search_engines)()
            engine_name = engine.__class__.__name__
            if not engine_name in engine_times:
                break
            time_since_last_use = (
                datetime.now() - engine_times[engine_name]).total_seconds()
            if time_since_last_use < ENGINE_COOLDOWN_TIME:
                prush("Engine '{}' used too recently. Trying another...".format(
                    engine_name))
            else:
                break

        engine.set_headers({'User-Agent': get_random_user_agent()})
        # internally intepreted as sleep(random_uniform(*self._delay))
        # This value set low (or zero) since we pause between use of each
        # engine (above).
        engine._delay = (0, 0)
        subject = random.choice(subjects) + " news"
        prush("Searching for subject '{}'...".format(subject))
        search_results = engine.search(subject, pages=SEARCH_PAGES).links()
        engine_times[engine_name] = datetime.now()
        prush("Found {} results for subject '{}'.".format(
            len(search_results), subject))
        return search_results

    success_count = 0
    search_results = _search()
    while success_count < doc_count:
        if success_count % 10 == 0:
            prush("\n{}: {} docs processed. {}% complete.\n".format(
                datetime.now(), success_count, 100 * round(success_count / doc_count, 2)))
        if success_count % SUBJECT_BATCH_SIZE == 0 and success_count != 0:
            search_results = _search()
        # We try to maintain a buffer above the minumum number of results required
        # so we 1) can choose some results at random (not just take all results) and
        # 2) can account for the fact that some of the links will not return 200.
        if len(search_results) < SUBJECT_BATCH_SIZE * 2:
            prush("Not enough results for subject. Trying another...")
            search_results = _search()
            continue
        success = False
        while not success:
            if len(search_results) == 0:
                prush("Exhausted search results for this subject. Trying another...")
                break
            random.seed()
            search_result = random.choice(search_results)
            search_results.remove(search_result)
            prush("Accessing {}...".format(search_result))
            if "youtube.com" in search_result:
                prush("  Appears to be a YouTube result. Trying another...")
                continue
            if search_result[:-3] == "pdf":
                prush("  Appears to be a PDF. Trying another...")
                continue
            file_name = os.path.join(
                os.getcwd(), destination_dir, hash(search_result) + ".txt")
            if os.path.exists(file_name):
                prush("  URL previously ingested. Trying another...")
                continue
            try:
                pass
                # with time_limit(REQUEST_TIMEOUT):
                #     response = urllib.request.urlopen(search_result)
                # raw_document = bytes(doc.Doc(response.read()).clean, 'utf-8')
                # document = raw_document.decode("utf-8", "strict")
            except Exception as e:
                prush("  Error. {}\n  Trying another...".format(e))
                continue
            success = True
            success_count = success_count + 1
    prush(datetime.now(), "Done")


def prush(*args):
    print(*args)
    sys.stdout.flush()


class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()

# Copyright 2021 Joe Colasurdo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import sys
import random
from datetime import datetime
import csv

from googlesearch import get_random_user_agent
from search_engines import *

# Minimum wait time between calling an engine for different searches (in
# seconds)
ENGINE_COOLDOWN_TIME = 5
# The number of pages worth of search results to consider from each search
# attempt.
SEARCH_PAGES = 1
NO_TIPS_PLACEHOLDER = "No tips submitted for this location yet"

PREFERRED_SEARCH_TEMPLATE = "site:gov {} County {} covid vaccine access"
ALTERNATE_SEARCH_TEMPLATE = "{} County {} covid vaccine access"

search_engines = [
    Ask,
    Bing,
    Dogpile,
    Duckduckgo,
    # Google really really hates being scraped. You can uncomment it but even
    # with the search engine randomization and pacing their heuristics tend to
    # ban scapers really quickly.
    # Google,
    Mojeek,
    Startpage,
    Yahoo
]


def main():
    with open('county_list.csv', newline='') as f:
        r = csv.reader(f, delimiter=',')
        for row in r:
            county, state = row[0], row[1]
            prush("{}, {}...".format(county, state))

            engine_times = dict()
            time_since_last_use = 0
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
            subject = PREFERRED_SEARCH_TEMPLATE.format(county, state)
            search_results = engine.search(subject, pages=SEARCH_PAGES).links()

            if len(search_results) == 0:
                subject = ALTERNATE_SEARCH_TEMPLATE.format(
                    county, state)
                search_results = engine.search(
                    subject, pages=SEARCH_PAGES).links()

            engine_times[engine_name] = datetime.now()

            title = fmt_title(engine_name, subject)
            access_time = fmt_access_time()

            markdown = ""
            with open(state + "/" + county + ".md", "r") as county_file:
                markdown = county_file.read()

            if len(search_results) == 0 or search_results[0] in markdown:
                continue

            uri = search_results[0]

            if len(markdown.strip()) == 0 or NO_TIPS_PLACEHOLDER in markdown.lower():
                markdown = fmt_page_heading(county, state)

            markdown = markdown + fmt_entry(title, uri, access_time)

            with open(state + "/" + county + ".md", "w") as county_file:
                county_file.write(markdown)


def fmt_title(engine_name, subject):
    return "{} Search for '{}'".format(engine_name, subject)


def fmt_access_time():
    return "Retrieved on {}".format(
        datetime.utcnow().strftime("%A, %B %-d, %Y at %-I:%M%p (UTC)"))


def fmt_page_heading(county, state):
    return "## Covid tips for {}, {}".format(county, state)


def fmt_entry(title, uri, access_time):
    return "\n\n{}\n{}\n{}".format(title, uri, access_time)


def prush(*args):
    """prush is a print followed by a flush"""
    print(*args)
    sys.stdout.flush()


if __name__ == "__main__":
    main()

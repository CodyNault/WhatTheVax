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
import time

from googlesearch import get_random_user_agent
from search_engines import *

# The minimum cooldown period between successive preferred search calls to the
# same engine.
ENGINE_MIN_COOLDOWN_SECS = 3.0

# If the preferred search template does not return unseful results, the same
# engine will be called a second time with an alternate search template.  A
# 'random' waiting period is imposed between the preferred and alternate calls
# to reduce the likelyhood of getting rate-limited.
ALTERNATE_SEARCH_MIN_WAIT_SECS = 0.2
ALTERNATE_SEARCH_MAX_WAIT_SECS = 1.0

# The number of pages worth of search results to consider from each search
# attempt.
SEARCH_PAGES = 1

# This is not case sensitive.
NO_TIPS_PLACEHOLDER = "No tips submitted for this location yet"

# The ideal search phrase to use to extract desired information.  If this
# phrase fails to provide useful results, the alternate template is used.
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
    Startpage,
    Yahoo
]


def main():
    with open('county_list.csv', newline='') as f:
        engine_times = dict()
        r = csv.reader(f, delimiter=',')
        for row in r:
            county, state = replace_underscores(row[0]), replace_underscores(row[1])
            prush("{}, {}...".format(county, state))

            time_since_last_use = 0
            engine_name = ""
            while True:
                # This does basically constitute a busy loop if all engines are
                # in a cooldown period, but since this is single threaded, I'm
                # not too concerned.
                engine = random.choice(search_engines)()
                engine_name = engine.__class__.__name__
                if not engine_name in engine_times:
                    break
                time_since_last_use = (
                    datetime.now() - engine_times[engine_name]).total_seconds()
                if time_since_last_use >= ENGINE_MIN_COOLDOWN_SECS:
                    break

            engine.set_headers({'User-Agent': get_random_user_agent()})
            subject = PREFERRED_SEARCH_TEMPLATE.format(county, state)
            search_results = engine.search(subject, pages=SEARCH_PAGES).links()
            engine_times[engine_name] = datetime.now()

            if len(search_results) == 0:
                subject = ALTERNATE_SEARCH_TEMPLATE.format(
                    county, state)

                # Random-uniform wait period between successive calls to same
                # engine adds some delay and jitter to the calls, making it
                # just slightly harder to get rate-limited.
                time.sleep(random.uniform(
                    ALTERNATE_SEARCH_MIN_WAIT_SECS, ALTERNATE_SEARCH_MAX_WAIT_SECS))

                search_results = engine.search(
                    subject, pages=SEARCH_PAGES).links()

            title = fmt_title(engine_name, subject)
            access_time = fmt_access_time()
                
            markdown = ""
            with open(state + "/" + county + ".md", "r") as county_file:
                markdown = county_file.read()

            if len(search_results) == 0 or search_results[0] in markdown:
                continue

            uri = select_best_search_result(search_results)

            if len(markdown.strip()) == 0 or NO_TIPS_PLACEHOLDER.lower() in markdown.lower():
                markdown = fmt_page_heading(county, state)

            markdown = markdown + fmt_entry(title, uri, access_time)

            with open(state + "/" + county + ".md", "w") as county_file:
                county_file.write(markdown)


def select_best_search_result(search_results):
    # currently implemented to just return the top result, this could be
    # extended in any number of ways.
    return search_results[0]


def replace_underscores(s):
    return s.replace("_", " ")


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

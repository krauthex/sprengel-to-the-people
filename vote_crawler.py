#!/usr/bin/env python

import bs4
import time
import asyncio
import aiohttp
import argparse

# argparse setup
parser = argparse.ArgumentParser(description="Fetch voting data from "
                                             "municipality websites.")
parser.add_argument("urlfile", type=str,
                    help="Path to textfile containing the URLs.")
parser.add_argument("--outfile", type=str, default="voting_results",
                    help="Path to out file. (Default: %(default)s.csv)")
parser.add_argument("--append", action="store_true",
                    help="Append the data to the given out file path.")
parser.add_argument("--brokenurlfile", type=str, default="broken_urls.txt",
                    help="Specify filepath for broken urls. (always "
                         "overwritten)")
args = parser.parse_args()


# create outfile values
writeOption = "a" if args.append else "w"
outfile = args.outfile if args.outfile.endswith(".csv") else f"{args.outfile}.csv"

# data
with open(args.urlfile, "r") as f:
    urls = [l.strip() for l in f.readlines()]



def substringIndex(sub: str, l: list) -> int:
    """Return the first list index where substring `s` was found."""
    for i, s in enumerate(l):
        if sub in s:
            return i

def isSubstring(sub: str, l: list) -> bool:
    """Return True if `s` substring in any of the strings in list `l`."""
    return any([sub in i for i in l])

# extractor
def votingTableExtractor(content,
                         parties = ("ÖVP", "SPÖ", "FPÖ", "NEOS", "JETZT",
                                    "GRÜNE", "WANDL"),
                         alternatives = {"GRÜNE": "DIE GRÜNEN",
                                         "WANDL": "WANDEL",
                                         "JETZT": "JETZT - LISTE PILZ"}):
    """Extract voting results from `response` object.

    Search on the website's table (hardcoded to second appearing table on website due to website
    schema) for results of the parties listed in `parties`. If not found, try one of the
    `alternatives`.
    Returns empty dictionary if no table is found, otherwise a dictionary of (party, vote result)
    pairs.
    """
    # response = req.get(url)
    soup = bs4.BeautifulSoup(content, features="lxml")
    tables = soup.findAll("table")  # list of all html tables on website

    result = {}

    if tables == [] or len(tables) < 2:  # sanity check
        return result

    # funnily, the right table (if existent) always is the second table on the website (tables[1])
    fullTable = [d.text.upper().replace(",", ".") for d in tables[1].findAll("td")]

    for p in parties:
        if p in fullTable:  # find party in party-tuple
            result[p] = fullTable[fullTable.index(p)+1]

		# find party with alternative name
        elif (p in alternatives.keys()) and (alternatives[p] in fullTable):
            result[p] = fullTable[fullTable.index(alternatives[p])+1]

        # find party as part of alternative name e.g. "ÖVP Liste Kurz"
        elif isSubstring(p, fullTable):
            result[p] = fullTable[substringIndex(p, fullTable)+1]

        else:  # party wasn't found (or municipality was stupid), can't fill in data
            result[p] = "-"

    return result


# getting website content
async def fetchContent(session, url: str):
    async with session.get(url) as response:
        # print(response.text)
        content = await response.text()
    return votingTableExtractor(content)

# getting content for all websites
tasks = []
async def collectVotingData(urls: list):
    async with aiohttp.ClientSession() as session:
        # tasks = []
        for url in urls:
            tasks.append(asyncio.create_task(fetchContent(session, url)))
        await asyncio.gather(*tasks, return_exceptions=True)

def nameFromURL(url: str) -> tuple:
    parts = url.split('.')
    name = parts[1]
    sprengel = parts[-1].split("detailonr=")[1].split('&')[0]
    return name, sprengel

## results
ORDER = ("ÖVP", "SPÖ", "FPÖ", "NEOS", "JETZT", "GRÜNE", "WANDL")
rowtemplate = "{}," * 7 + "{}\n"

brokenMunicipalities = []

if __name__ == "__main__":
    start = time.time()
    asyncio.run(collectVotingData(urls))
    duration = time.time() - start

    print(f":: Finished {len(urls)} Sprengels in {duration} seconds.")

    start = time.time()
    with open(outfile, writeOption) as f:
        f.write(rowtemplate.format("Gemeinde-Sprengel", *ORDER))  # header for csv file
        for u, t in zip(urls, tasks):
            name, sprengel = nameFromURL(u)
            r = t.result()
            if r == {}:
                brokenMunicipalities.append(u)
            else:
                sortedResults = [r[p] for p in ORDER]
                f.write(rowtemplate.format(f"{name}-{sprengel}",
                                           *sortedResults))

    print(f":: Failed to retrieve voting data for {len(brokenMunicipalities)}"
          " sprengels.")

    with open("broken_municipalities.txt", 'w') as f:
        for l in brokenMunicipalities:
            f.write(f"{l}\n")
    duration = time.time() - start

    print(f":: Writing data to files took {duration} seconds.")
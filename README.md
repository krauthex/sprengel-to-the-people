# sprengel-to-the-people
A python script to fetch data of voting results on judical district (Sprengel) level.

## Usage
```console
$ ./vote_crawler.py --help
usage: vote_crawler.py [-h] [--outfile OUTFILE] [--append]
                       [--brokenurlfile BROKENURLFILE]
                       urlfile

Fetch voting data from municipality websites.

positional arguments:
  urlfile               Path to textfile containing the URLs.

optional arguments:
  -h, --help            show this help message and exit
  --outfile OUTFILE     Path to out file. (Default: voting_results.csv)
  --append              Append the data to the given out file path.
  --brokenurlfile BROKENURLFILE
                        Specify filepath for broken urls. (always overwritten)
```

The `urlfile` should contain urls in the form:
```
http://www.<municipality name>[.gv].at/system/web/wahl.aspx?detailonr=<sprengel specific number>&cmd=tabelle&menuonr=<website specific number>
```

e.g. `http://www.alberndorf.at/system/web/wahl.aspx?detailonr=226168008&cmd=tabelle&menuonr=220314917`.

Urls with a different format might work content-wise, but the script will then fail to read the municipality's name + sprengel identification number from the url.

## Notes
Sometimes not all urls work on the first try of script; these will be written to a file named (by default) `broken_municipalities.txt`. You can re-run the script with the `broken_municipalities.txt` file as `urlfile` and passing the `--append` option, to add newly found content to your `outfile`. "Not working" in this context means that the website is not reachable. If a website always lands in the `broken_municipalities.txt` file even after the second or third script run, the requested site is likely to be unreachable or not existent anymore.

## Results
The results are in a `.csv` file that has this schema (and sample result):
```
Gemeinde-Sprengel,ÖVP,SPÖ,FPÖ,NEOS,JETZT,GRÜNE,WANDL
alberndorf-226168008,911 (43.63%),338 (16.19%),388 (18.58%),142 (6.80%),32 (1.53%),260 (12.45%),8 (0.38%)
...
```

## Known issues
Some municipalities don't conform to the proper naming conventions of parties and thus the script fails to find the right value for the right party, e.g. the `ÖVP` being mislabeled as `Liste Sebastian Kurz`.
A few alternatives have been added to the script, but definitely not all of them.

Additionally, some municipalities don't even upload their results in an `html` table - rather, they have pdfs, screenshots of tabels or urls to other sites. In any of the above cases, the script fails and the resulting line in the `.csv` looks like
```
<municipality-sprengel number>,-,-,-,-,-,-,-
```

## Dependencies
`Python >= 3.7`, `aiohttp`, `BeautifulSoup4`
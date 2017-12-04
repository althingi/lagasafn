# Lagasafn

This repository contains an unofficial copy of [the Law Collection of Iceland](https://www.althingi.is/lagasafn/).

A [ZIP archive](https://www.althingi.is/lagasafn/zip-skra-af-lagasafni/) of the law collection is fetched, extracted and stored in the `html/` folder.

An attempt is made to parse the `.html` files to `.md` files which are stored in the `md/` folder.

Unfortunately the HTML structure is bad, to the point that parsing the content correctly to `.md` can be tricky.

## What's the reason for this repository?

In my opinion the Alþingi lagasafn is in great need of more love and care. The Icelandic public has access to the lagasafn as a set of `.html` files whose HTML structure is very lacking. It is, in my opinion, hard to navigate through, hard to figure out in which chapter a given law resides, and near impossible to lookup changesets between versions without using some diff tool of your own.

I conclude this, our lagasafn and its underlying assembly is in great need for cleanup, I propose the following:

* use `git` repository for version control
* maintain set of markdown files instead of HTML files

### Why markdown?

For the same reason most software documentation is written in markdown. It's minimalistic and contains only content with minimal structure and no styling. Plus it's easily parsable to structured HTML if needed.

## Requirements

`Python 2.7`, `pip` and pip modules listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

## Usage

```bash
# runs the althingi lagasafn CLI
python lagasafn.py
```

## Tests

```bash
# runs all tests
python runtests.py
```

## Todo

* Automate periodic law collection fetching, parsing and pushing to this repository
* Parse law pages better
  - detect content difference between file in `html` and `md`
  - figure out how the `md` file should look like
  - add parsing test for the file to folder `test/expamples` and file `test/test_webparser.py`
  - fix parser code in `lagasafn.py` so all tests pass
* Add CLI commands
* Refactoring?
  - split `lagasafn.py` file into smaller ones
  - smarter parsing

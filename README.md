# Blinkist scraper

## Introduction
This tool is a scraper for the Blinkist website.
It will grab all the 'blinks' (book summaries) from the Blinkist website and store them as epub files.

The code only works with a valid license to Blinkist!
Use username and password in scrape.py to log in.

## Running the tool
The code is built with `Python 3.9`.

To install the required packages:

* With anaconda:
    ```bash
    conda install -c conda-forge genshi
    conda install --yes --file requirements.txt
    ```
* With pip:
    ```bash
    pip install -r requirements.txt    
    ```

To run:
PYTHONPATH=. python3 scrape.py

#!/usr/bin/env python

import argparse
import logging
import re
import requests
import os


def get_item(text):
    pattern = r'<a\s+href=[\'"]?([^<>\'"]*?)[\'"]?>(.*)</[^<>]+>'
    match = re.search(pattern, text, flags = re.I | re.S | re.M)
    if match:
        link = match.group(1)
        name = match.group(2)
        return (link, name)


def process_input_file(infile):
    items = []
    with open(infile) as fd:
        for l in fd.readlines():
            item = get_item(l)
            items.append(item)
    return items


def get_target_file_name(uri, headers):
    disposition = headers['content-disposition']
    if disposition is not None:
        pattern = r'filename=[\'"]?([^\'"]+)[\'"]?'
        match = re.search(pattern, disposition, flags = re.I | re.S | re.M)
        if match:
            file_name = match.group(1)
        return file_name


def get_temp_file_name(uri, headers):
    match = re.search(r'cluster_id=(\d+)', uri, flags = re.I | re.S | re.M)
    if match:
        file_id = match.group(1)
    else:
        file_id = ''
    return "temp_file_" + file_id


def fetch_one_file(base_url, item):
    (uri, description) = item
    logging.debug('fetch_one_file, uri: %s, desc: %s' % (uri, description))
    url = base_url + uri
    resp = requests.get(url, stream=True)
    if not resp.ok:
        logging.error('fetch_one_file, request error, %s' % resp.reason)
    else:
        target_file_name = get_target_file_name(uri, resp.headers)
        temp_file_name = get_temp_file_name(uri, resp.headers)
        with open(temp_file_name, 'wb') as fd:
            for block in resp.iter_content(32 * 1024):
                fd.write(block)
        if target_file_name is not None:
            os.rename(temp_file_name, target_file_name)
        else:
            os.remove(temp_file_name)


def fetch_items(base_url, items):
    for item in items:
        fetch_one_file(base_url, item)


def main(args):
    items = process_input_file(args.infile)
    fetch_items(args.base_url, items)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--infile')
    parser.add_argument('-o', '--outfile')
    parser.add_argument('-b', '--base_url')
    parser.add_argument('-d', '--debug', default='info')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    debug_level = args.debug.upper()
    logging.basicConfig(format='%(asctime)s %(message)s', level=debug_level)
    main(args)


#!/usr/bin/env python3

from typing import Any, Dict, List
from urllib.parse import urlencode
import aiohttp
import pandas as pd


BaseUrl = 'https://www.loc.gov/search/'
PerPage = 150  # highest allowed value, says result.pagination.perpage_options
MaxNRecords = PerPage * 5  # because we don't want jobs running forever


Partofs = [
    # Be careful: keep in sync with JSON
    # If you reorder or delete, you'll need a migrate_params().
    #
    # Full list: https://www.loc.gov/search/index/partof/
    None,
    'bills',
    'house bills',
    'senate bills',
    'house resolutions',
    'senate resolutions',
    'federal register',
]


class Column:
    def __init__(self, key, name, parse_value=str):
        self.key = key
        self.name = name
        self.parse_value = parse_value

    def parse_series(self, records: List[Dict[str, Any]]) -> pd.Series:
        values = []
        for record in records:
            value = record.get(self.key)
            if value is not None:
                value = self.parse_value(value)
            values.append(value)

        return pd.Series(values, name=self.name)


Columns = [
    Column('id', 'id'),
    Column('title', 'Title'),
    Column('contributor', 'Contributor', lambda arr: '; '.join(arr)),
    Column('subject', 'Subject', lambda arr: '; '.join(arr)),
    Column('original_format', 'Original format', lambda arr: '; '.join(arr)),
    Column('location', 'Location', lambda arr: '; '.join(arr)),
    Column('description', 'Description', lambda arr: '; '.join(arr)),
    Column('date', 'Date'),  # str for now -- dunno how LoC formats them all
    Column('number_lccn', 'LCCN', lambda arr: '; '.join(arr)),
    Column('language', 'Languages', lambda arr: '; '.join(arr)),
]


async def _fetch_paginated(q: str, fa: str):
    qsparams = {
        'q': q,
        'fo': 'json',
        'c': PerPage,  # count per page
        'at': 'results,pagination',
    }
    if fa:
        qsparams['fa'] = fa
    pages = []

    async with aiohttp.ClientSession() as session:
        while True:
            url = BaseUrl + '?' + urlencode({
                **qsparams,
                'sp': len(pages) + 1,  # page number, 1-based
            })
            print(repr(url))
            async with session.get(url, raise_for_status=True) as response:
                data = await response.json()
                records = data['results']

                pages.append(pd.DataFrame(dict(
                    (c.name, c.parse_series(records)) for c in Columns
                )))

                n_fetched = PerPage * len(pages)
                n_total = data['pagination']['of']

                if n_fetched >= n_total or n_fetched >= MaxNRecords:
                    break

    return pd.concat(pages)


async def fetch(params):
    q = params['q']

    if not q:
        return (None, 'Missing search phrase')

    facets = []

    try:
        partof = Partofs[params['partof']]
        if partof:
            facets.append(f'partof:{partof}')
    except IndexError:
        pass

    if facets:
        fa = '|'.join(facets)
    else:
        fa = None

    try:
        return await _fetch_paginated(q, fa)
    except aiohttp.client_exceptions.ClientResponseError as err:
        return (
            'HTTP error from Library of Congress server: %(code)d %(message)s'
            % {'code': err.code, 'message': err.message}
        )

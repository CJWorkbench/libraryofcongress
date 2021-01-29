#!/usr/bin/env python3

import io
import json
from typing import Any, Dict, List
from urllib.parse import urlencode

import cjwmodule.http
import cjwmodule.http.client
import pandas as pd


BaseUrl = "https://www.loc.gov/search/"
PerPage = 150  # highest allowed value, says result.pagination.perpage_options
MaxNRecords = PerPage * 5  # because we don't want jobs running forever


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
    Column("id", "id"),
    Column("title", "Title"),
    Column("contributor", "Contributor", lambda arr: "; ".join(arr)),
    Column("subject", "Subject", lambda arr: "; ".join(arr)),
    Column("original_format", "Original format", lambda arr: "; ".join(arr)),
    Column("location", "Location", lambda arr: "; ".join(arr)),
    Column("description", "Description", lambda arr: "; ".join(arr)),
    Column("date", "Date"),  # str for now -- dunno how LoC formats them all
    Column("number_lccn", "LCCN", lambda arr: "; ".join(arr)),
    Column("language", "Languages", lambda arr: "; ".join(arr)),
]


async def _fetch_paginated(q: str, fa: str):
    qsparams = {
        "q": q,
        "fo": "json",
        "c": PerPage,  # count per page
        "at": "results,pagination",
    }
    if fa:
        qsparams["fa"] = fa
    pages = []

    while True:
        buf = io.BytesIO()
        url = (
            BaseUrl
            + "?"
            + urlencode(
                {
                    **qsparams,
                    "sp": len(pages) + 1,  # page number, 1-based
                }
            )
        )
        await cjwmodule.http.client.download(url, buf)  # raise HttpError
        data = json.loads(buf.getvalue().decode("utf-8"))
        records = data["results"]

        pages.append(
            pd.DataFrame(dict((c.name, c.parse_series(records)) for c in Columns))
        )

        n_fetched = PerPage * len(pages)
        n_total = data["pagination"]["of"]

        if n_fetched >= n_total or n_fetched >= MaxNRecords:
            break

    return pd.concat(pages, ignore_index=True)


async def fetch(params):
    q = params["q"]

    if not q:
        return (None, "Missing search phrase")

    facets = []
    if params["partof"] != "entire_library":
        # menu values are all snake-case strings, like 'house_bills'. Convert
        # to what library of congress uses: spaces in names, like 'house bills'
        partof = params["partof"].replace("_", " ")
        facets.append(f"partof:{partof}")
    if facets:
        fa = "|".join(facets)
    else:
        fa = None

    try:
        return await _fetch_paginated(q, fa)
    except cjwmodule.http.HttpError as err:
        return [err.i18n_message]


def _migrate_params_v0_to_v1(params):
    """
    v0: partof indexes into "|bills|house_bills|senate_bills|house_resolutions
                             |senate_resolutions|federal_register"

    v1: values themselves.
    """
    return {
        **params,
        "partof": [
            "entire_library",
            "bills",
            "house_bills",
            "senate_bills",
            "house_resolutions",
            "senate_resolutions",
            "federal_register",
        ][params["partof"]],
    }


def migrate_params(params):
    if isinstance(params["partof"], int):
        params = _migrate_params_v0_to_v1(params)
    return params

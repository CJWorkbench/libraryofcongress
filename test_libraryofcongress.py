#!/usr/bin/env python3

import asyncio
import unittest
from libraryofcongress import fetch, migrate_params


class FetchTest(unittest.TestCase):
    def test_integration(self):
        async def go():
            result = await fetch({'q': 'football', 'partof': 0})
            print(repr(result))

        loop = asyncio.new_event_loop()
        loop.run_until_complete(go())
        loop.close()


class MigrateParamsTest(unittest.TestCase):
    def test_v0_no_partof(self):
        self.assertEqual(migrate_params({
            'q': 'baseball',
            'partof': 0,
            'version_select': '',
        }), {
            'q': 'baseball',
            'partof': '',
            'version_select': '',
        })

    def test_v0_with_partof(self):
        self.assertEqual(migrate_params({
            'q': 'baseball',
            'partof': 2,
            'version_select': '',
        }), {
            'q': 'baseball',
            'partof': 'house bills',
            'version_select': '',
        })

    def test_v1(self):
        self.assertEqual(migrate_params({
            'q': 'baseball',
            'partof': 'house bills',
            'version_select': '',
        }), {
            'q': 'baseball',
            'partof': 'house bills',
            'version_select': '',
        })

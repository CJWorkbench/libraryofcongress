#!/usr/bin/env python3

import asyncio
import unittest
from libraryofcongress import fetch


class FetchTest(unittest.TestCase):
    def test_integration(self):
        async def go():
            result = await fetch({'q': 'football', 'partof': 0})
            print(repr(result))

        loop = asyncio.new_event_loop()
        loop.run_until_complete(go())
        loop.close()

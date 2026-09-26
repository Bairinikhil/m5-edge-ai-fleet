import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fleet


class FleetTests(unittest.TestCase):
    def test_topic_parsing(self):
        self.assertEqual(fleet.parse_topic('devices/m5-01/health'), ('m5-01', 'health'))
        self.assertIsNone(fleet.parse_topic('bad/topic'))

    def test_store_event_and_fleet_count(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(fleet, 'DB_PATH', Path(folder) / 'fleet.db'):
                fleet.init_db()
                self.assertTrue(fleet.store_event('devices/m5-01/inference',
                    json.dumps({'device_id': 'm5-01', 'state': 'STILL'}).encode()))
                self.assertFalse(fleet.store_event('devices/m5-01/inference',
                    json.dumps({'device_id': 'other'}).encode()))
                self.assertEqual(fleet.health()['devices'], 1)
                self.assertEqual(fleet.health()['events'], 1)

    def test_bad_json_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(fleet, 'DB_PATH', Path(folder) / 'fleet.db'):
                fleet.init_db()
                self.assertFalse(fleet.store_event('devices/m5-01/health', b'not-json'))


if __name__ == '__main__':
    unittest.main()

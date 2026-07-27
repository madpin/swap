import unittest
from datetime import date

from aio import (
    SWAP_EVENT_DATE_PROPERTY,
    SWAP_EVENT_PROPERTIES,
    delete_swap_events,
    is_swap_event,
    process_shifts,
)


class FakeCalendarManager:
    def __init__(self, events_by_date=None, all_events=None):
        self.events_by_date = events_by_date or {}
        self.all_events = all_events or []
        self.created_events = []
        self.deleted_event_ids = []
        self.requested_dates = []
        self.list_from_date = None

    def get_events_date(self, date):
        self.requested_dates.append(date.isoformat())
        return self.events_by_date.get(date.isoformat(), [])

    def list_events(self, from_date=None):
        self.list_from_date = from_date
        return self.all_events

    def create_event(self, **event):
        self.created_events.append(event)
        return event

    def delete_event(self, event_id):
        self.deleted_event_ids.append(event_id)
        return True


class SwapEventTests(unittest.TestCase):
    user_names = ["DrRachelKerry", "RACHEL"]

    def test_recognizes_tagged_and_legacy_events(self):
        tagged_event = {
            "extendedProperties": {
                "private": SWAP_EVENT_PROPERTIES,
            }
        }
        legacy_event = {"description": "DrRachelKerry - 2026-08-01\n08:00 - 17:00"}
        unrelated_event = {"description": "Personal appointment - 2026-08-01"}

        self.assertTrue(is_swap_event(tagged_event, self.user_names))
        self.assertTrue(is_swap_event(legacy_event, self.user_names))
        self.assertFalse(is_swap_event(unrelated_event, self.user_names))

    def test_overwrite_deletes_only_swap_events(self):
        manager = FakeCalendarManager(
            all_events=[
                {
                    "id": "tagged",
                    "extendedProperties": {
                        "private": SWAP_EVENT_PROPERTIES,
                    },
                },
                {
                    "id": "legacy",
                    "description": "Rachel - 2026-08-01\nOFF",
                },
                {
                    "id": "manual",
                    "summary": "Dentist",
                    "description": "Personal appointment",
                },
                {
                    "id": "past",
                    "description": "Rachel - 2026-07-31\nOFF",
                },
            ]
        )

        deleted_count = delete_swap_events(
            manager,
            self.user_names,
            from_date=date(2026, 8, 1),
        )

        self.assertEqual(deleted_count, 2)
        self.assertEqual(manager.deleted_event_ids, ["tagged", "legacy"])
        self.assertEqual(manager.list_from_date, date(2026, 8, 1))

    def test_sync_replaces_owned_events_and_cleans_blank_dates(self):
        manager = FakeCalendarManager(
            events_by_date={
                "2026-08-01": [
                    {
                        "id": "outdated-shift",
                        "summary": "Hospital",
                        "description": "Rachel - 2026-08-01\n08:00 - 16:00",
                    },
                    {
                        "id": "manual",
                        "summary": "Dentist",
                        "description": "Personal appointment",
                    },
                ],
                "2026-08-02": [
                    {
                        "id": "blank-day-shift",
                        "summary": "Work",
                        "description": "Rachel - 2026-08-02\n09:00 - 17:00",
                    },
                    {
                        "id": "previous-night-shift",
                        "summary": "Work",
                        "description": "Rachel - 2026-08-01\n20:00 - 08:00",
                    },
                ],
                "2026-07-31": [
                    {
                        "id": "past-shift",
                        "summary": "Work",
                        "description": "Rachel - 2026-07-31\n09:00 - 17:00",
                    }
                ],
            }
        )
        parsed_rota = [
            {
                "name": "Rachel",
                "date": "2026-08-01",
                "raw_data": "10:00 - 18:00",
                "shift_type": "regular",
                "is_working": True,
                "start_date": "2026-08-01 10:00:00",
                "end_date": "2026-08-01 18:00:00",
            },
            {
                "name": "Rachel",
                "date": "2026-07-31",
                "raw_data": "09:00 - 17:00",
                "shift_type": "regular",
                "is_working": True,
                "start_date": "2026-07-31 09:00:00",
                "end_date": "2026-07-31 17:00:00",
            },
        ]

        process_shifts(
            manager,
            parsed_rota,
            self.user_names,
            covered_dates={"2026-07-31", "2026-08-01", "2026-08-02"},
            from_date=date(2026, 8, 1),
        )

        self.assertEqual(
            manager.deleted_event_ids,
            ["outdated-shift", "blank-day-shift"],
        )
        self.assertNotIn("manual", manager.deleted_event_ids)
        self.assertNotIn("past-shift", manager.deleted_event_ids)
        self.assertNotIn("previous-night-shift", manager.deleted_event_ids)
        self.assertNotIn("2026-07-31", manager.requested_dates)
        self.assertEqual(len(manager.created_events), 1)
        self.assertEqual(
            manager.created_events[0]["private_properties"][SWAP_EVENT_DATE_PROPERTY],
            "2026-08-01",
        )
        self.assertTrue(
            SWAP_EVENT_PROPERTIES.items()
            <= manager.created_events[0]["private_properties"].items()
        )

    def test_sync_keeps_one_identical_event_and_removes_duplicates(self):
        description = "Rachel - 2026-08-03\nOFF"
        manager = FakeCalendarManager(
            events_by_date={
                "2026-08-03": [
                    {
                        "id": "keep",
                        "summary": "Off",
                        "description": description,
                    },
                    {
                        "id": "duplicate",
                        "summary": "Off",
                        "description": description,
                    },
                ]
            }
        )
        parsed_rota = [
            {
                "name": "Rachel",
                "date": "2026-08-03",
                "raw_data": "OFF",
                "shift_type": "off",
                "is_working": False,
            }
        ]

        process_shifts(
            manager,
            parsed_rota,
            self.user_names,
            from_date=date(2026, 8, 1),
        )

        self.assertEqual(manager.deleted_event_ids, ["duplicate"])
        self.assertEqual(manager.created_events, [])


if __name__ == "__main__":
    unittest.main()

"""
test_app.py - Automated verification tests for Audixa backend, database, and API routes.
"""

import os
import sys
import unittest
import json
import io

# Import app modules
import db
import transcriber
from app import app


class TestAudixaBackend(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_01_db_crud(self):
        """Test SQLite DB creation, insert, retrieve, and update."""
        tx_id = "test_tx_001"
        segments = [
            {"id": "seg_1", "start_time": 0.0, "end_time": 4.5, "text": "Hello world"},
            {"id": "seg_2", "start_time": 4.5, "end_time": 9.0, "text": "Testing second segment"}
        ]
        chapters = [
            {"id": "ch_1", "title": "Introduction", "start_time": 0.0, "end_time": 4.5},
            {"id": "ch_2", "title": "Second Part", "start_time": 4.5, "end_time": 9.0}
        ]

        db.save_full_transcript(
            transcript_id=tx_id,
            filename="sample.mp3",
            original_name="sample.mp3",
            language_mode="en",
            detected_language="en",
            duration=9.0,
            model_size="tiny",
            segments=segments,
            chapters=chapters
        )

        # Retrieve
        fetched = db.get_transcript_by_id(tx_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(len(fetched["segments"]), 2)
        self.assertEqual(len(fetched["chapters"]), 2)
        self.assertEqual(fetched["segments"][0]["text"], "Hello world")

        # Update segment text
        segments[0]["text"] = "Hello world updated"
        db.save_transcript_segments(tx_id, segments)
        fetched2 = db.get_transcript_by_id(tx_id)
        self.assertEqual(fetched2["segments"][0]["text"], "Hello world updated")

        # Update chapters
        chapters.append({"id": "ch_3", "title": "New Chapter", "start_time": 2.0, "end_time": 4.0})
        saved_ch = db.save_chapters(tx_id, chapters)
        # Should be auto-sorted by start_time: 0.0 -> 2.0 -> 4.5
        self.assertEqual(len(saved_ch), 3)
        self.assertEqual(saved_ch[1]["title"], "New Chapter")

    def test_02_routes_get(self):
        """Test GET endpoints for HTML templates."""
        res_index = self.client.get("/")
        self.assertEqual(res_index.status_code, 200)
        self.assertIn(b"Audixa", res_index.data)
        self.assertIn(b"Dropzone", res_index.data.replace(b"dropzone", b"Dropzone"))

        res_editor = self.client.get("/editor?id=test_tx_001")
        self.assertEqual(res_editor.status_code, 200)
        self.assertIn(b"WaveSurfer", res_editor.data)

    def test_03_api_endpoints(self):
        """Test API endpoints /transcript/<id>, /save_transcript, /save_chapters."""
        # GET transcript
        res = self.client.get("/transcript/test_tx_001")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["id"], "test_tx_001")

        # Save transcript
        new_segs = [{"id": "seg_1", "start_time": 0.0, "end_time": 4.5, "text": "Modified text via API"}]
        res_save_tx = self.client.post("/save_transcript/test_tx_001", json={"segments": new_segs})
        self.assertEqual(res_save_tx.status_code, 200)

        # Save chapters
        new_chaps = [{"id": "ch_1", "title": "API Chapter", "start_time": 0.0, "end_time": 9.0}]
        res_save_ch = self.client.post("/save_chapters/test_tx_001", json={"chapters": new_chaps})
        self.assertEqual(res_save_ch.status_code, 200)

        # Verify persistence
        res_verify = self.client.get("/transcript/test_tx_001")
        data_v = res_verify.get_json()
        self.assertEqual(data_v["data"]["segments"][0]["text"], "Modified text via API")
        self.assertEqual(data_v["data"]["chapters"][0]["title"], "API Chapter")

    def test_04_upload_flow(self):
        """Test /upload route with actual test.mp3."""
        sample_path = os.path.join(os.path.dirname(__file__), "backend", "test.mp3")
        if not os.path.exists(sample_path):
            sample_path = os.path.join(os.path.dirname(__file__), "test.mp3")

        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                audio_bytes = f.read()

            data = {
                "file": (io.BytesIO(audio_bytes), "test.mp3"),
                "language_mode": "auto",
                "model_size": "tiny"
            }

            res = self.client.post("/upload", data=data, content_type="multipart/form-data")
            self.assertEqual(res.status_code, 200)
            res_json = res.get_json()
            self.assertTrue(res_json["success"])
            self.assertIn("id", res_json)
            self.assertIn("redirect_url", res_json)
            print(f"\n[Test Result] Generated Transcript ID: {res_json['id']}")


if __name__ == "__main__":
    unittest.main()

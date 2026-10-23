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

    def test_05_segment_split_and_merge(self):
        """Test API endpoints for splitting and merging transcript segments."""
        tx_id = "test_tx_split_merge"
        segments = [
            {"id": "seg_split_1", "start_time": 0.0, "end_time": 6.0, "text": "This is a sentence to split in half"},
            {"id": "seg_split_2", "start_time": 6.0, "end_time": 10.0, "text": "And this is the following sentence"}
        ]
        chapters = [{"id": "ch_1", "title": "Intro", "start_time": 0.0, "end_time": 10.0}]

        db.save_full_transcript(
            transcript_id=tx_id,
            filename="split_test.mp3",
            original_name="split_test.mp3",
            language_mode="en",
            detected_language="en",
            duration=10.0,
            model_size="tiny",
            segments=segments,
            chapters=chapters
        )

        # Test Split
        res_split = self.client.post(
            f"/api/split_segment/{tx_id}",
            json={"segment_id": "seg_split_1", "split_time": 3.0}
        )
        self.assertEqual(res_split.status_code, 200)
        split_data = res_split.get_json()
        self.assertTrue(split_data["success"])
        self.assertEqual(len(split_data["segments"]), 3)
        self.assertEqual(split_data["segments"][0]["end_time"], 3.0)
        self.assertEqual(split_data["segments"][1]["start_time"], 3.0)

        # Test Merge
        res_merge = self.client.post(
            f"/api/merge_segments/{tx_id}",
            json={"segment_id": split_data["segments"][0]["id"]}
        )
        self.assertEqual(res_merge.status_code, 200)
        merge_data = res_merge.get_json()
        self.assertTrue(merge_data["success"])
        self.assertEqual(len(merge_data["segments"]), 2)

    def test_06_regenerate_chapters(self):
        """Test automatic chapter regeneration from pause gaps."""
        tx_id = "test_tx_chaps"
        segments = [
            {"id": "s1", "start_time": 0.0, "end_time": 10.0, "text": "Welcome to our podcast."},
            {"id": "s2", "start_time": 13.0, "end_time": 25.0, "text": "Today we discuss artificial intelligence."},
            {"id": "s3", "start_time": 30.0, "end_time": 50.0, "text": "Conclusion and summary."}
        ]
        db.save_full_transcript(
            transcript_id=tx_id,
            filename="chaps.mp3",
            original_name="chaps.mp3",
            language_mode="en",
            detected_language="en",
            duration=50.0,
            model_size="tiny",
            segments=segments,
            chapters=[]
        )

        res = self.client.post(f"/api/regenerate_chapters/{tx_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["chapters"]), 0)

    def test_07_export_endpoints(self):
        """Test exporting transcript to TXT, SRT, VTT, YouTube, MD, and JSON."""
        tx_id = "test_tx_export"
        segments = [
            {"id": "s1", "start_time": 0.0, "end_time": 2.5, "text": "Hello world."},
            {"id": "s2", "start_time": 2.5, "end_time": 5.0, "text": "Welcome to Audixa."}
        ]
        chapters = [{"id": "c1", "title": "Introduction", "start_time": 0.0, "end_time": 5.0}]
        db.save_full_transcript(
            transcript_id=tx_id,
            filename="export.mp3",
            original_name="export.mp3",
            language_mode="en",
            detected_language="en",
            duration=5.0,
            model_size="tiny",
            segments=segments,
            chapters=chapters
        )

        for fmt in ["txt", "srt", "vtt", "youtube", "md", "json", "pdf"]:
            res = self.client.get(f"/api/export/{tx_id}/{fmt}")
            self.assertEqual(res.status_code, 200, f"Export format {fmt} failed")
            self.assertGreater(len(res.data), 0)

    def test_08_history_and_health(self):
        """Test /api/history and /api/health endpoints."""
        res_h = self.client.get("/api/health")
        self.assertEqual(res_h.status_code, 200)
        self.assertEqual(res_h.get_json()["status"], "ok")

        res_hist = self.client.get("/api/history")
        self.assertEqual(res_hist.status_code, 200)
        data = res_hist.get_json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["history"], list)

    def test_09_multilingual_and_100_features(self):
        """Test 25+ language dictionary, translation flag, PDF plan route, and speaker attribution."""
        # 1. Verify 25+ languages
        self.assertGreaterEqual(len(transcriber.SUPPORTED_LANGUAGES), 25)
        self.assertIn("hi", transcriber.SUPPORTED_LANGUAGES)
        self.assertIn("es", transcriber.SUPPORTED_LANGUAGES)
        self.assertIn("ja", transcriber.SUPPORTED_LANGUAGES)
        self.assertIn("bn", transcriber.SUPPORTED_LANGUAGES)

        # 2. Verify /plan-100.pdf and /download/plan-100-pdf
        res_plan = self.client.get("/plan-100.pdf")
        self.assertEqual(res_plan.status_code, 200)
        self.assertEqual(res_plan.mimetype, "application/pdf")
        self.assertGreater(len(res_plan.data), 5000)

        res_dl = self.client.get("/download/plan-100-pdf")
        self.assertEqual(res_dl.status_code, 200)
        self.assertEqual(res_dl.mimetype, "application/pdf")

        # 3. Test speaker attribution in segments
        tx_id = "test_speaker_attr"
        segments = [
            {"id": "spk_1", "start_time": 0.0, "end_time": 3.0, "text": "Welcome to the show", "speaker": "Host"},
            {"id": "spk_2", "start_time": 3.0, "end_time": 6.0, "text": "Thanks for having me", "speaker": "Guest"}
        ]
        db.save_full_transcript(
            transcript_id=tx_id,
            filename="spk.mp3",
            original_name="spk.mp3",
            language_mode="auto",
            detected_language="en",
            duration=6.0,
            model_size="tiny",
            segments=segments,
            chapters=[],
            task_mode="transcribe"
        )
        fetched = db.get_transcript_by_id(tx_id)
        self.assertEqual(fetched["segments"][0]["speaker"], "Host")
        self.assertEqual(fetched["segments"][1]["speaker"], "Guest")

        # Test text export formatting with speakers
        res_txt = self.client.get(f"/api/export/{tx_id}/txt")
        self.assertIn(b"Host: Welcome to the show", res_txt.data)
        self.assertIn(b"Guest: Thanks for having me", res_txt.data)


if __name__ == "__main__":
    unittest.main()

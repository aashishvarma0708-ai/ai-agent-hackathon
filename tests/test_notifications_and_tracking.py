import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app as backend_app
from core.db import (
    init_db,
    save_complaint,
    get_complaint_by_tracking_token,
    update_notification_status,
)
from core.orchestrator import (
    normalize_phone_number,
    generate_tracking_token,
    process_complaint,
)
from callbot.app.sms_sender import normalize_phone as normalize_sms_phone, CivicResolveSMS
from callbot.app.whatsapp_sender import (
    normalize_whatsapp_phone,
    mask_phone,
    CivicResolveWhatsApp,
)
from callbot.app.main import app as callbot_app


class TestPhoneNormalization(unittest.TestCase):
    def test_normalize_phone_number_indian_formats(self):
        # 10 digit Indian numbers
        phone, err = normalize_phone_number("9876543210")
        self.assertEqual(phone, "+919876543210")
        self.assertIsNone(err)

        phone, err = normalize_phone_number(" 9876543210 ")
        self.assertEqual(phone, "+919876543210")

        phone, err = normalize_phone_number("09876543210")
        self.assertEqual(phone, "+919876543210")

        phone, err = normalize_phone_number("919876543210")
        self.assertEqual(phone, "+919876543210")

        phone, err = normalize_phone_number("+919876543210")
        self.assertEqual(phone, "+919876543210")

        phone, err = normalize_phone_number("+91 98765-43210")
        self.assertEqual(phone, "+919876543210")

        phone, err = normalize_phone_number("(+91) 98765 43210")
        self.assertEqual(phone, "+919876543210")

    def test_normalize_phone_number_international(self):
        phone, err = normalize_phone_number("+14155552671")
        self.assertEqual(phone, "+14155552671")
        self.assertIsNone(err)

        phone, err = normalize_phone_number("+447911123456")
        self.assertEqual(phone, "+447911123456")
        self.assertIsNone(err)

    def test_normalize_phone_number_invalid(self):
        phone, err = normalize_phone_number("")
        self.assertIsNone(phone)
        self.assertIsNone(err)

        phone, err = normalize_phone_number(None)
        self.assertIsNone(phone)
        self.assertIsNone(err)

        phone, err = normalize_phone_number("123")
        self.assertIsNone(phone)
        self.assertIsNotNone(err)

        phone, err = normalize_phone_number("invalid_phone")
        self.assertIsNone(phone)
        self.assertIsNotNone(err)

    def test_whatsapp_phone_normalization(self):
        self.assertEqual(normalize_whatsapp_phone("9876543210"), "whatsapp:+919876543210")
        self.assertEqual(normalize_whatsapp_phone("+919876543210"), "whatsapp:+919876543210")
        self.assertEqual(normalize_whatsapp_phone("whatsapp:+919876543210"), "whatsapp:+919876543210")
        self.assertEqual(normalize_whatsapp_phone("+14155238886"), "whatsapp:+14155238886")

    def test_mask_phone(self):
        self.assertEqual(mask_phone("+919876543210"), "*********3210")
        self.assertEqual(mask_phone("whatsapp:+919876543210"), "whatsapp:*********3210")
        self.assertEqual(mask_phone("123"), "****")


class TestTrackingTokenGeneration(unittest.TestCase):
    def test_token_format_and_uniqueness(self):
        tokens = [generate_tracking_token() for _ in range(50)]
        for t in tokens:
            self.assertGreaterEqual(len(t), 40)
            self.assertTrue(t.replace("-", "").replace("_", "").isalnum())
        self.assertEqual(len(tokens), len(set(tokens)))


class TestDatabaseTracking(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_save_and_retrieve_by_tracking_token(self):
        token = generate_tracking_token()
        complaint = {
            "complaint_id": "CR-TEST-9999",
            "complaint_text": "Severe water logging on 5th main road",
            "location_text": "Ward 12, Indiranagar",
            "category": "drainage",
            "priority": "HIGH",
            "status": "NEW",
            "department": "Water Supply & Sewerage Board",
            "citizen_phone": "+919876543210",
            "notification_preference": "both",
            "whatsapp_opt_in": 1,
            "tracking_token": token,
        }
        save_complaint(complaint)

        retrieved = get_complaint_by_tracking_token(token)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["complaint_id"], "CR-TEST-9999")
        self.assertEqual(retrieved["tracking_token"], token)
        self.assertEqual(retrieved["citizen_phone"], "+919876543210")
        self.assertEqual(retrieved["notification_preference"], "both")

        # Test updating notification status
        update_notification_status("CR-TEST-9999", sms_status="sent", whatsapp_status="sent")
        updated = get_complaint_by_tracking_token(token)
        self.assertEqual(updated["sms_last_status"], "sent")
        self.assertEqual(updated["whatsapp_last_status"], "sent")
        self.assertIsNotNone(updated["last_notification_at"])


class TestPublicTrackingAPI(unittest.TestCase):
    def setUp(self):
        init_db()
        self.client = TestClient(backend_app)

    def test_public_tracking_endpoint_success(self):
        token = generate_tracking_token()
        complaint = {
            "complaint_id": "CR-TRACK-101",
            "complaint_text": "Broken street lamp pole leaning dangerously",
            "location_text": "Cross 4, Sector 7",
            "category": "electricity",
            "priority": "HIGH",
            "status": "ASSIGNED",
            "department": "Electricity & Power Dept",
            "citizen_phone": "+919876543210",
            "notification_preference": "sms",
            "whatsapp_opt_in": 0,
            "tracking_token": token,
            "authority_notes": "INTERNAL SENSITIVE SUPERVISOR NOTE",
        }
        save_complaint(complaint)

        res = self.client.get(f"/api/public/track/{token}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["complaint_id"], "CR-TRACK-101")
        self.assertEqual(data["status"], "ASSIGNED")
        self.assertEqual(data["category"], "electricity")
        self.assertEqual(data["priority"], "HIGH")
        # Ensure sensitive internal authority notes are NOT exposed
        self.assertNotIn("INTERNAL SENSITIVE SUPERVISOR NOTE", str(data))
        self.assertNotIn("authority_notes", data)

    def test_public_tracking_endpoint_not_found(self):
        res = self.client.get("/api/public/track/non_existent_token_12345")
        self.assertEqual(res.status_code, 404)


class TestCallbotNotificationRoute(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(callbot_app)

    def test_notify_unauthorized(self):
        res = self.client.post("/internal/notify", json={
            "complaint_id": "CR-1234",
            "phone_number": "+919876543210",
        })
        self.assertEqual(res.status_code, 401)

    @patch("app.notification_routes.CivicResolveSMS")
    @patch("app.notification_routes.CivicResolveWhatsApp")
    def test_notify_authorized_multi_channel(self, MockWA, MockSMS):
        mock_sms = MagicMock()
        mock_wa = MagicMock()
        MockSMS.return_value = mock_sms
        MockWA.return_value = mock_wa

        secret = os.getenv("NOTIFICATION_SHARED_SECRET", "cr_notify_secret_2026")
        res = self.client.post(
            "/internal/notify",
            headers={"X-Notification-Secret": secret},
            json={
                "complaint_id": "CR-260826-5555",
                "phone_number": "+919876543210",
                "notification_preference": "both",
                "whatsapp_opt_in": True,
                "tracking_token": "test_token_abc",
                "evidence_url": "https://example.com/evidence/123",
            }
        )

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "processed")
        self.assertEqual(data["sms_status"], "sent")
        self.assertEqual(data["whatsapp_status"], "sent")
        mock_sms.send_complaint_links.assert_called_once()
        mock_wa.send_complaint_links.assert_called_once()


class TestMultiChannelSenders(unittest.TestCase):
    def test_sms_sender_complaint_links_format(self):
        with patch("callbot.app.sms_sender.Client") as MockClient:
            mock_twilio_instance = MagicMock()
            mock_message = MagicMock()
            mock_message.sid = "SM_MOCK_123"
            mock_message.status = "queued"
            mock_twilio_instance.messages.create.return_value = mock_message
            MockClient.return_value = mock_twilio_instance

            sms = CivicResolveSMS(
                account_sid="AC_MOCK",
                auth_token="AUTH_MOCK",
                from_number="+15005550006",
            )
            res = sms.send_complaint_links(
                to_number="9876543210",
                complaint_id="CR-260826-0001",
                evidence_url="https://example.com/evidence/tok123",
                tracking_url="https://example.com/track/tracktok456",
            )

            self.assertEqual(res["sid"], "SM_MOCK_123")
            mock_twilio_instance.messages.create.assert_called_once()
            called_kwargs = mock_twilio_instance.messages.create.call_args[1]
            self.assertEqual(called_kwargs["to"], "+919876543210")
            self.assertIn("CR-260826-0001", called_kwargs["body"])
            self.assertIn("https://example.com/evidence/tok123", called_kwargs["body"])
            self.assertIn("https://example.com/track/tracktok456", called_kwargs["body"])

    def test_whatsapp_sender_sandbox_format(self):
        with patch("callbot.app.whatsapp_sender.Client") as MockClient:
            mock_twilio_instance = MagicMock()
            mock_message = MagicMock()
            mock_message.sid = "WA_MOCK_123"
            mock_message.status = "queued"
            mock_twilio_instance.messages.create.return_value = mock_message
            MockClient.return_value = mock_twilio_instance

            wa = CivicResolveWhatsApp(
                account_sid="AC_MOCK",
                auth_token="AUTH_MOCK",
                from_number="whatsapp:+14155238886",
                sandbox_mode=True,
            )
            res = wa.send_complaint_links(
                to_number="+919876543210",
                complaint_id="CR-260826-0002",
                evidence_url="https://example.com/evidence/tok123",
                tracking_url="https://example.com/track/tracktok456",
            )

            self.assertEqual(res["sid"], "WA_MOCK_123")
            mock_twilio_instance.messages.create.assert_called_once()
            called_kwargs = mock_twilio_instance.messages.create.call_args[1]
            self.assertEqual(called_kwargs["to"], "whatsapp:+919876543210")
            self.assertIn("CivicResolve AI", called_kwargs["body"])
            self.assertIn("CR-260826-0002", called_kwargs["body"])
            self.assertIn("https://example.com/evidence/tok123", called_kwargs["body"])
            self.assertIn("https://example.com/track/tracktok456", called_kwargs["body"])


if __name__ == "__main__":
    unittest.main()

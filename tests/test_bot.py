import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import dr_multiservices_bot as bot


def update(text="Test"):
    return SimpleNamespace(message=SimpleNamespace(text=text, reply_text=AsyncMock()),
                           effective_user=SimpleNamespace(id=1, username="test"))


class FlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_command_entry_points(self):
        ctx = SimpleNamespace(user_data={"prefilled_service": "Old"})
        self.assertEqual(await bot.devis_command(update(), ctx), bot.QUOTE_NAME)
        self.assertNotIn("prefilled_service", ctx.user_data)
        self.assertEqual(await bot.rdv_command(update(), ctx), bot.APPOINTMENT_NAME)

    async def test_invalid_phone_and_email_do_not_advance(self):
        ctx = SimpleNamespace(user_data={"quote": {}, "appointment": {}})
        self.assertEqual(await bot.quote_get_phone(update("abc"), ctx), bot.QUOTE_PHONE)
        self.assertEqual(await bot.appointment_get_phone(update("abc"), ctx), bot.APPOINTMENT_PHONE)
        self.assertEqual(await bot.quote_get_email(update("wrong"), ctx), bot.QUOTE_EMAIL)
        self.assertEqual(ctx.user_data["quote"], {})

    async def test_complete_quote_saved_and_draft_cleared(self):
        ctx = SimpleNamespace(user_data={"prefilled_service": "Climatisation"})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quotes.json"
            with patch.object(bot, "QUOTES_FILE", path):
                await bot.quote_get_name(update("Client test"), ctx)
                await bot.quote_get_phone(update("+212661234567"), ctx)
                self.assertEqual(await bot.quote_get_email(update("test@example.com"), ctx), bot.QUOTE_SURFACE)
                await bot.quote_get_surface(update("50 m2"), ctx)
                await bot.quote_get_address(update("Marrakech"), ctx)
                self.assertEqual(await bot.quote_get_details(update("Installation"), ctx), -1)
                self.assertEqual(bot.load_data(path)[0]["service"], "Climatisation")
        self.assertNotIn("quote", ctx.user_data)

    async def test_cancel_clears_only_form_data(self):
        ctx = SimpleNamespace(user_data={"quote": {}, "appointment": {}, "prefilled_service": "x", "other": 1})
        await bot.cancel_conversation(update(), ctx)
        self.assertEqual(ctx.user_data, {"other": 1})

    async def test_no_key_uses_local_fallback(self):
        item = update("Bonjour")
        with patch.object(bot, "client", None):
            await bot.handle_message(item, SimpleNamespace(user_data={}))
        self.assertIn("/devis", item.message.reply_text.call_args.args[0])

    async def test_group_callback_does_not_collect_data(self):
        query = SimpleNamespace(answer=AsyncMock(), data="request_quote_general",
                                message=SimpleNamespace(reply_text=AsyncMock()))
        item = SimpleNamespace(callback_query=query, effective_chat=SimpleNamespace(type="group"))
        self.assertEqual(await bot.button_callback(item, SimpleNamespace(user_data={})), -1)
        query.message.reply_text.assert_awaited_once()


class StorageTests(unittest.TestCase):
    def test_atomic_failure_preserves_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            bot.save_data(path, [{"name": "قديم"}])
            with patch.object(bot.os, "replace", side_effect=OSError("disk")):
                with self.assertRaises(OSError):
                    bot.save_data(path, [{"name": "new"}])
            self.assertEqual(bot.load_data(path), [{"name": "قديم"}])
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_registered_conversation_commands(self):
        with patch.dict(os.environ, {key: "" for key in ("ALL_PROXY", "HTTPS_PROXY", "HTTP_PROXY", "all_proxy", "https_proxy", "http_proxy")}), patch.object(bot, "TELEGRAM_BOT_TOKEN", "123456:test"):
            app = bot.build_application()
        conv = app.handlers[0][0]
        self.assertEqual(conv.entry_points[0].commands, frozenset({"devis"}))
        self.assertEqual(conv.entry_points[1].commands, frozenset({"rdv"}))
        self.assertTrue(conv.allow_reentry)


if __name__ == "__main__":
    unittest.main()

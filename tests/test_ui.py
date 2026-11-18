import json
import socket
import unittest

from heocr_desktop import app, i18n, offline, render


class RenderTest(unittest.TestCase):
    def test_constructs(self):
        md = ("<!-- page 1 -->\n\n# כותרת\n\nשורה אחת  \nשורה שתיים\n\n| א | ב |\n|---|---|\n| 1 | 2\\|3 |\n\n"
              "---\n\n**הערות**\n\n<!-- heocr: unread (time_limit) -->")
        html = render.to_html(md, "Page")
        self.assertIn('<div class="page-mark">Page 1</div>', html)
        self.assertIn('<h1 dir="auto">כותרת</h1>', html)
        self.assertIn("שורה אחת<br>שורה שתיים", html)
        self.assertIn("<td>2|3</td>", html)
        self.assertIn("<hr>", html)
        self.assertIn("<strong>הערות</strong>", html)
        self.assertIn('class="note"', html)

    def test_everything_escaped(self):
        html = render.to_html('<script>alert(1)</script>\n\n# <img src=x onerror=y>\n\n| <b> |\n|---|')
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("<b>", html)


class StringsTest(unittest.TestCase):
    def test_same_keys_in_both_languages(self):
        self.assertEqual(set(i18n.STRINGS["en"]), set(i18n.STRINGS["he"]))
        self.assertEqual(i18n.STRINGS["he"]["dir"], "rtl")

    def test_system_language_is_known(self):
        self.assertIn(i18n.system_language(), i18n.STRINGS)

    def test_page_has_no_remote_content(self):
        page = app.page_html("he")
        self.assertIn("default-src 'none'", page)
        for bad in ("http://", "https://", "src=\"//", "@import"):
            self.assertNotIn(bad, page)
        boot = page.split("const BOOT = ", 1)[1].split(";\n", 1)[0]
        self.assertEqual(json.loads(boot.replace("<\\/", "</"))["lang"], "he")


class OfflineTest(unittest.TestCase):
    def test_remote_connections_refused(self):
        offline.enforce()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with self.assertRaises(offline.OfflineError):
                s.connect(("93.184.215.14", 443))
            with self.assertRaises(offline.OfflineError):
                socket.getaddrinfo("example.org", 443)
        finally:
            s.close()

    def test_loopback_allowed(self):
        offline.enforce()
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            c.connect(srv.getsockname())
        finally:
            c.close()
            srv.close()


if __name__ == "__main__":
    unittest.main()

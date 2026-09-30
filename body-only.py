# -*- coding: utf-8 -*-

from burp import IBurpExtender, IMessageEditorTabFactory, IMessageEditorTab

from java.awt import Color, Font
from java.lang import Runnable
from javax.swing import JTextPane, JScrollPane, SwingUtilities
from javax.swing.text import SimpleAttributeSet, StyleConstants

import json
import re


class UiTask(Runnable):

    def __init__(self, action):
        self.action = action

    def run(self):
        self.action()


class ColoredBodyEditor(object):

    TOKENS = re.compile(
        r'"(?:\\.|[^"\\])*"'
        r'|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
        r'|\b(?:true|false|null)\b'
    )

    def __init__(self, callbacks):
        self.helpers = callbacks.getHelpers()

        self.pane = JTextPane()
        callbacks.customizeUiComponent(self.pane)

        self.pane.setFont(Font("Monospaced", Font.PLAIN, 16))
        self.pane.setEditable(False)

        self.component = JScrollPane(self.pane)

        background = self.pane.getBackground()
        dark = (
            background.getRed()
            + background.getGreen()
            + background.getBlue()
        ) < 384

        self.normal = self.makeStyle(self.pane.getForeground())

        # Red: JSON property names.
        self.key = self.makeStyle(
            Color(255, 120, 120) if dark else Color(175, 35, 35)
        )

        # Green: string values.
        self.string = self.makeStyle(
            Color(130, 210, 140) if dark else Color(30, 125, 55)
        )

        # Blue: numbers, booleans, and null.
        self.literal = self.makeStyle(
            Color(140, 180, 255) if dark else Color(45, 85, 190)
        )

    @staticmethod
    def makeStyle(color):
        attributes = SimpleAttributeSet()
        StyleConstants.setForeground(attributes, color)
        return attributes

    def getComponent(self):
        return self.component

    def setText(self, data, highlight=False):
        # Preserve the original one-byte-to-one-character mapping.
        text = (
            unicode(self.helpers.bytesToString(data))
            if data is not None else u""
        )

        def update():
            document = self.pane.getStyledDocument()
            document.remove(0, document.getLength())
            document.insertString(0, text, self.normal)

            # Highlight only successfully parsed, ASCII-escaped JSON.
            # ASCII ensures Python and Swing character offsets agree.
            if highlight:
                for match in self.TOKENS.finditer(text):
                    token = match.group(0)

                    if token.startswith('"'):
                        remaining = text[match.end():].lstrip()

                        if remaining.startswith(":"):
                            attributes = self.key
                        else:
                            attributes = self.string
                    else:
                        attributes = self.literal

                    document.setCharacterAttributes(
                        match.start(),
                        match.end() - match.start(),
                        attributes,
                        True
                    )

            self.pane.setCaretPosition(0)

        if SwingUtilities.isEventDispatchThread():
            update()
        else:
            SwingUtilities.invokeLater(UiTask(update))

    def getSelectedText(self):
        selected = self.pane.getSelectedText()

        if selected is None:
            return None

        return self.helpers.stringToBytes(selected)


class BurpExtender(IBurpExtender, IMessageEditorTabFactory):

    def registerExtenderCallbacks(self, callbacks):
        self.callbacks = callbacks

        callbacks.setExtensionName("Body Only (Colored JSON)")
        callbacks.registerMessageEditorTabFactory(self)
        callbacks.printOutput("Body Only (Colored JSON) loaded.")

    def createNewInstance(self, controller, editable):
        return BodyOnlyTab(self.callbacks)


class BodyOnlyTab(IMessageEditorTab):

    GUARDS = [
        r"^\s*for\s*\(\s*;\s*;\s*\)\s*;\s*",
        r"^\s*while\s*\(\s*(?:1|true)\s*\)\s*;\s*",
        r"^\s*\)\]\}',?\s*",
        r"^\s*/\*\*/\s*",
    ]

    def __init__(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self._original = None
        self._editor = ColoredBodyEditor(callbacks)

    def getTabCaption(self):
        return "Body Only"

    def getUiComponent(self):
        return self._editor.getComponent()

    def isEnabled(self, content, isRequest):
        return content is not None and not isRequest

    def setMessage(self, content, isRequest):
        self._original = content

        if content is None or isRequest:
            self._editor.setText(None)
            return

        display_bytes = None
        highlight = False

        try:
            response_info = self._helpers.analyzeResponse(content)
            offset = response_info.getBodyOffset()
            body_bytes = content[offset:]

            # Fall back to the original body if formatting fails.
            display_bytes = body_bytes

            raw = unicode(self._helpers.bytesToString(body_bytes))
            raw = raw.encode("iso-8859-1")

            charset = "utf-8"

            for header in response_info.getHeaders():
                header = unicode(header)

                if header.lower().startswith("content-type:"):
                    match = re.search(
                        r"""charset\s*=\s*["']?([^;"'\s]+)""",
                        header,
                        re.I
                    )

                    if match:
                        charset = match.group(1)

                    break

            try:
                body = raw.decode(charset)
            except (LookupError, UnicodeError):
                # A strict fallback avoids silently changing JSON values.
                body = raw.decode("utf-8")

            candidate = body.lstrip(u"\ufeff")

            for guard in self.GUARDS:
                candidate = re.sub(
                    guard,
                    "",
                    candidate,
                    count=1
                )

            try:
                parsed = json.loads(candidate.strip())

                display = json.dumps(
                    parsed,
                    indent=2,
                    ensure_ascii=True
                )

                display_bytes = self._helpers.stringToBytes(display)
                highlight = True

            except ValueError:
                # Non-JSON bodies remain unformatted.
                pass

        except (LookupError, UnicodeError):
            # Undecodable bodies remain unformatted.
            pass

        except Exception as error:
            self._callbacks.printError(
                "Body Only error: " + str(error)
            )

        self._editor.setText(display_bytes, highlight=highlight)

    def getMessage(self):
        # Always return the original HTTP message.
        return self._original

    def isModified(self):
        return False

    def getSelectedData(self):
        return self._editor.getSelectedText()

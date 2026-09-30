# Body Only — Colored JSON for Burp Suite

A lightweight Burp Suite extension that adds a **Body Only** response tab with pretty-printed JSON, syntax highlighting, and a **Monospaced 16 pt** font.

Inspect response bodies without HTTP headers while keeping the original HTTP message unchanged.

## Features

- Dedicated response-body tab.
- Pretty-printed JSON with two-space indentation.
- Red property names and green string values.
- Blue numbers, booleans, and `null`.
- Color palettes for light and dark editor backgrounds.
- Monospaced 16 pt font.
- Read-only display with selectable text.
- Support for common JSON guard prefixes.
- Charset detection from the response's `Content-Type` header.
- Unformatted fallback for non-JSON or undecodable bodies.

## Requirements

- Burp Suite with support for Python extensions through the legacy Extender API.
- Jython 2.7 standalone JAR configured in Burp.

This extension runs inside Burp through Jython. It is not a standalone Python 3 program and does not require pip packages.

## Installation

1. Download `body_only.py` from this repository.
2. Download the standalone JAR from the [Jython downloads page](https://www.jython.org/download).
3. Open Burp's **Settings → Extensions → Python environment**.
4. Set the location of the Jython standalone JAR.
5. Go to **Extensions → Installed** and click **Add**.
6. Select **Python** as the extension type.
7. Select `body_only.py` and complete the loading dialog.

Older Burp versions may place these options under **Extender**.

After loading, the extension output should show:

```text
Body Only (Colored JSON) loaded.
```

For additional setup guidance, see PortSwigger's [extension settings](https://portswigger.net/burp/documentation/desktop/settings/extensions) and [manual installation guide](https://portswigger.net/burp/documentation/desktop/extend-burp/extensions/installing/manual-install).

## Usage

1. Open an HTTP response in Burp, such as a response in Proxy history or Repeater.
2. Select the **Body Only** tab.
3. View the formatted and highlighted JSON.

The tab appears for responses only. Non-JSON bodies are displayed without JSON formatting.

### Example

Original body:

```json
{"status":"ok","count":2,"active":true,"items":["first","second"]}
```

Formatted body:

```json
{
  "status": "ok",
  "count": 2,
  "active": true,
  "items": [
    "first",
    "second"
  ]
}
```

GitHub uses its own syntax colors for these examples. The extension uses the following colors:

| JSON element | Color |
| --- | --- |
| Property names | Red |
| String values | Green |
| Numbers | Blue |
| Booleans and `null` | Blue |
| Punctuation | Editor foreground |

## Supported JSON Guards

The extension removes these common prefixes from the display candidate before attempting to parse JSON:

```text
for (;;);
while (1);
while (true);
)]}'
/**/
```

It also accepts a comma after the `)]}'` prefix.

Guard removal affects the formatted display only. The original HTTP message remains unchanged.

## Customization

### Font size

Edit this line in `ColoredBodyEditor.__init__`:

```python
self.pane.setFont(Font("Monospaced", Font.PLAIN, 16))
```

Replace `16` with your preferred font size, save the file, and reload the extension.

The font does not automatically follow Burp's message-editor font setting.

### Colors

Edit the `Color(red, green, blue)` values assigned to:

```python
self.key
self.string
self.literal
```

Each color has a dark-background and a light-background value. The palette is selected when the editor is created.

Reload the extension after making changes.

## Behavior and Limitations

- The view is read-only and returns the original HTTP message to Burp.
- Pretty-printing changes only the displayed representation.
- Parsing and re-serializing JSON can change number formatting, escape sequences, and object-key order, and can collapse duplicate keys. Use Burp's original response view when exact representation matters.
- Non-ASCII JSON characters appear as escapes such as `\u00e9`.
- Non-JSON fallback uses a byte-to-character mapping rather than a decoded Unicode or hex view.
- The extension does not implement decompression or HTTP transfer decoding. JSON formatting depends on the bytes provided by Burp.
- The custom editor does not include Burp's built-in search bar or other native message-editor features.
- HTML, XML, JavaScript, and malformed JSON are not beautified.
- Very large response bodies may slow down formatting and highlighting.

## Troubleshooting

### Extension fails to load

Confirm that the Jython standalone JAR is configured and that the extension type is set to **Python**. Check the extension's error output for details.

### Body Only tab is missing

Select an HTTP response. The tab is intentionally disabled for requests.

### JSON is not colored

The body must parse as JSON after any supported guard prefix is removed. Check for malformed JSON, unsupported prefixes, or compressed content.

### Font changes are not visible

Confirm that you edited the file loaded by Burp. Reload the extension and reopen the response.

## Development

Built with:

- Burp's legacy Extender API
- Jython
- Java Swing



# Installation

## Requirements

- Python 3.10 or newer
- pip

## Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/randheimer/PDF-Fusion.git
   cd PDF-Fusion
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the application:

   ```bash
   python main.py
   ```

## Dependencies

| Package | Required | Purpose |
|---------|----------|---------|
| `Pillow` | yes | Image handling and PDF pages for images |
| `customtkinter` | yes | The user interface |
| `pypdf[crypto]` | yes | Reading and merging PDF pages. The `crypto` extra adds AES decryption. |
| `PyMuPDF` (1.24.3 or newer) | optional | PDF thumbnails and previews |
| `tkinterdnd2` | optional | Drag & drop from Explorer |

PyMuPDF releases before 1.24.3 only provide the `fitz` module name, which this version does not import.

# Changelog

All notable changes to PDF Fusion are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [semantic versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - not released yet

### Added

- Merge PDF files and images (JPG, JPEG and PNG) into one PDF, in list order.
- Reorder files by dragging their thumbnails, remove single files, clear all, and paste an image from the clipboard.
- Preview of the selected file, scaled to fit the window.
- Drag & drop from Explorer, when tkinterdnd2 is installed.
- Interface in English, German and Swiss German. The Windows display language is used when it is supported, otherwise English.
- Portable Windows executable, built by GitHub Actions.

### Changed

- The user interface is built with CustomTkinter.
- PyPDF2 is replaced by pypdf.
- Python 3.10 or newer is required.

### Fixed

- Unsupported files chosen in the file dialog are rejected with a message.
- An export error names the file that caused it. Clicks during an export no longer change the file list.
- Thumbnails are cached, so reordering stays fast.
- Unreadable images get a "?" placeholder and their error is logged.
- Temp files from pasted images and failed exports are removed.
- The preview fits the window, and the layout no longer shifts with the image size.
- Drag & drop returns the accepted action, so Windows accepts the drop.

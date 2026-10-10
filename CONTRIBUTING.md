# 🤝 Contributing to PDF Fusion

Thanks for your interest in PDF Fusion. Every contribution is welcome.

## 🚀 How can I contribute?

### Reporting bugs
- Check first whether the bug is already in the [issue list](https://github.com/randheimer/PDF-Fusion/issues).
- Open a new issue with a clear description.
- Add screenshots if possible.
- Describe the steps to reproduce the problem, and include your Windows and Python versions.

### Suggesting features
- Open an issue with the label `enhancement`.
- Describe the feature in detail and explain why it would be useful.

### Contributing code

#### 1. Fork and clone
```bash
git clone https://github.com/<your-username>/PDF-Fusion.git
cd PDF-Fusion
```

#### 2. Set up a development environment
```bash
python -m venv venv
venv\Scripts\activate        # Linux/macOS: source venv/bin/activate
pip install Pillow PyPDF2 PyMuPDF tkinterdnd2 pycryptodome
```

#### 3. Create a branch
Use a short, descriptive name, for example `fix/export-error` or `feature/dark-mode`.
```bash
git checkout -b feature/my-new-feature
```

#### 4. Make your changes
- Follow the style of the surrounding code.
- Add comments for complex logic.
- Test your changes thoroughly.

#### 5. Commit and push
```bash
git add .
git commit -m "Describe your change"
git push origin feature/my-new-feature
```

#### 6. Open a pull request
- Describe your changes clearly.
- Link related issues, for example `Closes randheimer/PDF-Fusion#12`.
- Wait for a review.

## 📝 Code guidelines

### Style
- Use type hints where possible.
- Follow PEP 8.
- Keep lines to 100 characters or fewer.
- Use descriptive variable names.

### Documentation
- Add docstrings to public functions.
- Write code comments and UI texts in English.
- Update the README when you add a feature.

### Testing
- Test on Windows, the platform the project is developed on. Testers on Linux and macOS are welcome.
- Test with and without the optional dependencies.
- Test with files of different sizes and formats.

## 🐛 Known issues

See the [issue list](https://github.com/randheimer/PDF-Fusion/issues) for current problems and planned features.

## 💡 Ideas for contributions

- Translations into other languages
- Additional file formats (TIFF, BMP, etc.)
- PDF editing features (rotate, crop)
- Batch processing
- A command-line interface
- Unit tests
- Performance improvements

## 📧 Contact

Open an issue, or contact the maintainer via GitHub.

---

Thanks for helping make PDF Fusion better! 🎉

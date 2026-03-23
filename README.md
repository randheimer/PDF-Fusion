# 📄 PDF Fusion

Eine moderne, benutzerfreundliche Desktop-Anwendung zum Zusammenführen von PDFs und Bildern in ein einziges PDF-Dokument.

Läuft komplett lokal auf Ihrem Rechner (ohne Cloud, lokal wie localhost), speichert niemals Daten auf fremden Servern.

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## ✨ Features

- **📁 Mehrere Dateiformate**: Unterstützt PDF, JPG, JPEG und PNG
- **🖱️ Drag & Drop**: Intuitive Bedienung durch Ziehen und Ablegen von Dateien
- **🔄 Neuanordnung**: Einfaches Umordnen der Dateien per Drag & Drop
- **👁️ Live-Vorschau**: Sofortige Vorschau der ausgewählten Dateien
- **📋 Zwischenablage**: Bilder direkt aus der Zwischenablage einfügen
- **🎨 Moderne UI**: Ansprechendes, dunkles Design mit klarer Struktur
- **⚡ Schnell & Effizient**: Optimierte Verarbeitung auch großer Dateien

## 📸 Screenshots

```
┌─────────────────────────────────────────────────────────┐
│  📄 PDF Fusion                                          │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  [Buttons]   │           Vorschau-Bereich               │
│              │                                          │
│  Thumbnails  │                                          │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

## 🚀 Installation

### Voraussetzungen

- Python 3.7 oder höher
- pip (Python Package Manager)

### Schritt 1: Repository klonen

```bash
git clone https://github.com/randheimer/pdf-fusion.git
cd pdf-fusion
```

### Schritt 2: Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### Schritt 3: Anwendung starten

```bash
python main.py
```

## 📦 Abhängigkeiten

### Erforderlich
- `Pillow` - Bildverarbeitung
- `PyPDF2` - PDF-Manipulation

### Optional (für erweiterte Funktionen)
- `PyMuPDF` (fitz) - Verbesserte PDF-Vorschau und -Rendering
- `tkinterdnd2` - Drag & Drop von externen Dateien

```bash
# Alle Abhängigkeiten installieren
pip install Pillow PyPDF2 PyMuPDF tkinterdnd2
```

## 💻 Verwendung

1. **Dateien hinzufügen**
   - Klicken Sie auf "➕ Dateien hinzufügen"
   - Oder ziehen Sie Dateien direkt in die Anwendung (wenn tkinterdnd2 installiert ist)

2. **Reihenfolge ändern**
   - Klicken und ziehen Sie Thumbnails, um die Reihenfolge zu ändern

3. **Vorschau anzeigen**
   - Doppelklicken Sie auf ein Thumbnail für eine größere Vorschau

4. **Aus Zwischenablage einfügen**
   - Kopieren Sie ein Bild
   - Klicken Sie auf "📋 Paste Clipboard"

5. **PDF erstellen**
   - Klicken Sie auf "💾 Als PDF speichern"
   - Wählen Sie den Speicherort

## 🛠️ Technische Details

### Architektur

```
PDF Fusion
│
├── main.py                 # Hauptanwendung
├── requirements.txt        # Python-Abhängigkeiten
├── README.md              # Dokumentation
└── LICENSE                # MIT-Lizenz
```

### Hauptkomponenten

- **PDFMergerApp**: Hauptklasse der Anwendung
  - GUI-Verwaltung mit Tkinter
  - Datei-Management
  - Thumbnail-Generierung
  - PDF-Export-Funktionalität

### Unterstützte Formate

| Format | Lesen | Schreiben | Vorschau |
|--------|-------|-----------|----------|
| PDF    | ✅    | ✅        | ✅       |
| JPG    | ✅    | ✅        | ✅       |
| JPEG   | ✅    | ✅        | ✅       |
| PNG    | ✅    | ✅        | ✅       |

## 🔧 Konfiguration

Die Anwendung verwendet folgende Standard-Einstellungen:

- **Fenstergröße**: 1200x700 Pixel
- **Minimale Größe**: 800x500 Pixel
- **Thumbnail-Größe**: 80x80 Pixel
- **Vorschau-Größe**: 600x600 Pixel
- **PDF-Qualität**: 95%
- **PDF-Auflösung**: 100 DPI

## 🐛 Fehlerbehebung

### PyMuPDF nicht installiert
Wenn PyMuPDF nicht verfügbar ist, werden PDF-Vorschauen als einfache Platzhalter angezeigt. Installieren Sie PyMuPDF für bessere PDF-Unterstützung:
```bash
pip install PyMuPDF
```

### Drag & Drop funktioniert nicht
Stellen Sie sicher, dass tkinterdnd2 installiert ist:
```bash
pip install tkinterdnd2
```

### Bilder werden nicht korrekt konvertiert
Die Anwendung konvertiert automatisch RGBA/LA/P-Bilder zu RGB. Bei Problemen überprüfen Sie das Bildformat.

## 🤝 Beitragen

Beiträge sind willkommen! So können Sie helfen:

1. Forken Sie das Repository
2. Erstellen Sie einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committen Sie Ihre Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Pushen Sie zum Branch (`git push origin feature/AmazingFeature`)
5. Öffnen Sie einen Pull Request

## 📝 Roadmap

- [ ] Unterstützung für weitere Bildformate (TIFF, BMP, GIF)
- [ ] PDF-Seiten einzeln bearbeiten
- [ ] Wasserzeichen hinzufügen
- [ ] Batch-Verarbeitung
- [ ] Kommandozeilen-Interface
- [ ] Portable .exe Version
- [ ] Mehrsprachige Unterstützung
- [ ] Dunkler/Heller Modus-Umschalter

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

## 👤 Autor

Erstellt mit ❤️ für die Open-Source-Community

## 🙏 Danksagungen

- [Pillow](https://python-pillow.org/) - Python Imaging Library
- [PyPDF2](https://pypdf2.readthedocs.io/) - PDF-Toolkit
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF-Rendering
- [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2) - Drag & Drop Support

## 📞 Support

Bei Fragen oder Problemen:
- Öffnen Sie ein [Issue](https://github.com/IhrUsername/pdf-fusion/issues)
- Kontaktieren Sie mich über GitHub

---

**Hinweis**: Dieses Projekt befindet sich in aktiver Entwicklung. Feedback und Vorschläge sind willkommen!

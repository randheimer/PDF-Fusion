"""
PDF Fusion - Ein moderner PDF-Editor für Windows
Ermöglicht das Zusammenführen von PDFs und Bildern zu einem PDF-Dokument.
"""

import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk, ImageGrab, ImageDraw
from PyPDF2 import PdfReader, PdfWriter

# Optionale Abhängigkeiten prüfen
try:
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False


# ═══════════════════════════════════════════════════════════════════════════
# KONSTANTEN
# ═══════════════════════════════════════════════════════════════════════════

# Farbschema
CLR_DARK = "#22303f"
CLR_PANEL = "#2a3f55"
CLR_LIGHT = "#f6f9fc"
CLR_BG = "#e9eff6"
CLR_GREEN = "#2aa650"
CLR_BLUE = "#2d8fca"
CLR_RED = "#d94836"
CLR_ORANGE = "#e67e22"
CLR_MUTED = "#5f6b77"

# Unterstützte Dateiformate
SUPPORTED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png")


# ═══════════════════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════

def _pdf_placeholder(size: tuple[int, int] = (80, 80)) -> Image.Image:
    """
    Erstellt ein graues Platzhalterbild für PDFs ohne Vorschau.
    
    Args:
        size: Tuple mit (Breite, Höhe) des Platzhalterbildes
        
    Returns:
        PIL Image Objekt mit grauem Hintergrund und "PDF" Text
    """
    img = Image.new("RGB", size, "lightgray")
    draw = ImageDraw.Draw(img)
    draw.text((size[0] // 2 - 10, size[1] // 2 - 5), "PDF", fill="black")
    return img


# ═══════════════════════════════════════════════════════════════════════════
# HAUPTKLASSE
# ═══════════════════════════════════════════════════════════════════════════

class PDFFusionApp:
    """
    Hauptanwendung für PDF Fusion.
    
    Ermöglicht das Hinzufügen, Sortieren und Zusammenführen von PDF- und Bilddateien
    zu einem einzigen PDF-Dokument mit grafischer Benutzeroberfläche.
    """
    
    def __init__(self, root: tk.Tk) -> None:
        """
        Initialisiert die Anwendung.
        
        Args:
            root: Tkinter Root-Fenster
        """
        self.root = root
        self._setup_window()

        # Datenverwaltung
        self.files: list[str] = []  # Liste aller hinzugefügten Dateipfade
        self.thumbnails: list[tk.Frame] = []  # Liste der Thumbnail-Widgets
        self.drag_data: dict = {  # Daten für Drag & Drop Operationen
            "index": None,
            "widget": None,
            "moved": False
        }

        self._setup_drag_and_drop()
        self._setup_keyboard_shortcuts()
        self._build_ui()

    def _setup_window(self) -> None:
        """Konfiguriert das Hauptfenster."""
        self.root.title("PDF Fusion")
        self.root.geometry("1200x700")
        self.root.minsize(800, 500)
        self.root.configure(bg=CLR_BG)

    def _setup_drag_and_drop(self) -> None:
        """Aktiviert Drag & Drop falls verfügbar."""
        if HAS_DND:
            try:
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind("<<Drop>>", self.drop_files)
            except Exception:
                pass

    def _setup_keyboard_shortcuts(self) -> None:
        """Registriert Tastaturkürzel."""
        self.root.bind("<Control-o>", lambda e: self.add_files())
        self.root.bind("<Control-v>", lambda e: self.paste_image())
        self.root.bind("<Control-s>", lambda e: self.save_pdf())
        self.root.bind("<Delete>", lambda e: self.clear_all())

    # ═══════════════════════════════════════════════════════════════════════
    # UI-AUFBAU
    # ═══════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        """Erstellt die gesamte Benutzeroberfläche."""
        # Linke Seitenleiste (Buttons + Thumbnails)
        self.left_frame = tk.Frame(self.root, width=340, bg=CLR_DARK)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.left_frame.pack_propagate(False)

        # Rechter Bereich (Vorschau)
        self.right_frame = tk.Frame(self.root, bg=CLR_LIGHT, padx=12, pady=12)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_sidebar()
        self._build_preview()
        self._build_statusbar()

    def _build_sidebar(self) -> None:
        """Erstellt die linke Seitenleiste mit Buttons und Thumbnail-Liste."""
        btn_frame = tk.Frame(self.left_frame, bg=CLR_DARK)
        btn_frame.pack(pady=10, padx=12, fill=tk.X)

        # Titel
        tk.Label(
            btn_frame, 
            text="PDF Fusion", 
            font=("Segoe UI", 17, "bold"),
            bg=CLR_DARK, 
            fg="white", 
            pady=6
        ).pack(pady=(0, 18), fill=tk.X)

        # Aktions-Buttons
        buttons = [
            ("➕  Dateien hinzufügen (Strg+O)", CLR_GREEN, ("Segoe UI", 10, "bold"), self.add_files),
            ("📋  Aus Zwischenablage (Strg+V)", CLR_BLUE, ("Segoe UI", 10, "bold"), self.paste_image),
            ("🗑️  Alle löschen (Entf)", CLR_RED, ("Segoe UI", 10, "bold"), self.clear_all),
            ("💾  Als PDF speichern (Strg+S)", CLR_ORANGE, ("Segoe UI", 11, "bold"), self.save_pdf),
        ]
        
        for i, (text, color, font, cmd) in enumerate(buttons):
            b = tk.Button(
                btn_frame, 
                text=text, 
                command=cmd,
                bg=color, 
                fg="white", 
                font=font,
                relief=tk.FLAT, 
                cursor="hand2", 
                activebackground="white",
                          activeforeground="black", bd=0)
            b.pack(pady=(10 if i == 0 else 6), fill=tk.X)

        # Scrollbarer Thumbnail-Bereich
        container = tk.Frame(self.left_frame, bg=CLR_PANEL, bd=0)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 12))

        self.canvas = tk.Canvas(container, bg=CLR_PANEL, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview,
                                 troughcolor=CLR_PANEL, bd=0, bg=CLR_PANEL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.thumb_frame = tk.Frame(self.canvas, bg=CLR_PANEL)
        self.canvas.create_window((0, 0), window=self.thumb_frame, anchor="nw")
        self.thumb_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>",   self._on_mousewheel)
        self.canvas.bind_all("<Button-5>",   self._on_mousewheel)

    def _build_preview(self) -> None:
        header = tk.Frame(self.right_frame, bg=CLR_PANEL, height=50, bd=0)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="Vorschau", font=("Segoe UI", 13, "bold"),
                 bg=CLR_PANEL, fg="white").pack(pady=12)

        preview_box = tk.Frame(self.right_frame, bg="white", bd=1, relief=tk.SOLID)
        preview_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(10, 8))

        self.preview_label = tk.Label(
            preview_box,
            text="Ziehe Dateien hierher\noder klicke auf 'Dateien hinzufügen'",
            bg="white", fg=CLR_MUTED, font=("Segoe UI", 12), justify=tk.CENTER
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.preview_instructions = tk.Label(
            self.right_frame,
            text="Klick auf ein Thumbnail zeigt Vorschau an • Ziehen zum Sortieren",
            bg=CLR_LIGHT, fg=CLR_MUTED, font=("Segoe UI", 10, "italic")
        )
        self.preview_instructions.pack(fill=tk.X, pady=(0, 6))

    def _build_statusbar(self) -> None:
        self.status_bar = tk.Label(
            self.root, text="Bereit  |  0 Dateien",
            bg=CLR_PANEL, fg="white", anchor="w", padx=14, pady=4,
            font=("Segoe UI", 10)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ── Datei-Verwaltung ───────────────────────────────────────────────────────

    def drop_files(self, event) -> None:
        """Verarbeitet per Drag & Drop hinzugefügte Dateien."""
        added_count = 0
        dropped_files = self.root.tk.splitlist(event.data)
        
        for file_path in dropped_files:
            if file_path.lower().endswith(SUPPORTED_EXTENSIONS):
                self.files.append(file_path)
                added_count += 1
        
        if added_count > 0:
            self.update_thumbnails()
            total_files = len(self.files)
            self.status_bar.config(
                text=f"{added_count} Datei(en) per Drag & Drop hinzugefügt  |  {total_files} gesamt"
            )

    def add_files(self) -> None:
        """Öffnet Dateiauswahl-Dialog und fügt ausgewählte Dateien hinzu."""
        selected_files = filedialog.askopenfilenames(
            title="Dateien auswählen",
            filetypes=[
                ("Bilder & PDFs", "*.jpg *.jpeg *.png *.pdf"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if selected_files:
            self.files.extend(selected_files)
            self.update_thumbnails()
            self.status_bar.config(
                text=f"{len(selected_files)} Datei(en) hinzugefügt  |  {len(self.files)} gesamt"
            )

    def clear_all(self) -> None:
        """Entfernt alle Dateien nach Bestätigung."""
        if not self.files:
            return
            
        if messagebox.askyesno("Bestätigung", "Alle Dateien entfernen?"):
            self.files.clear()
            self.update_thumbnails()
            self._reset_preview()
            self.status_bar.config(text="Alle Dateien entfernt  |  0 Dateien")
    
    def _reset_preview(self) -> None:
        """Setzt die Vorschau auf den Standardzustand zurück."""
        self.preview_label.config(
            image="",
            text="Ziehe Dateien hierher\noder klicke auf 'Dateien hinzufügen'"
        )

    def paste_image(self) -> None:
        """Fügt ein Bild aus der Zwischenablage hinzu."""
        try:
            clipboard_image = ImageGrab.grabclipboard()
            
            if isinstance(clipboard_image, Image.Image):
                # Speichere Bild temporär
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                clipboard_image.save(temp_file)
                
                self.files.append(temp_file)
                self.update_thumbnails()
                self.status_bar.config(
                    text=f"Bild aus Zwischenablage hinzugefügt  |  {len(self.files)} Datei(en)"
                )
            else:
                messagebox.showwarning(
                    "Einfügen",
                    "Kein Bild in der Zwischenablage gefunden."
                )
        except Exception as exc:
            messagebox.showerror("Fehler", f"Fehler beim Einfügen: {exc}")

    def delete_file(self, index: int) -> None:
        """Entfernt eine einzelne Datei an der angegebenen Position."""
        if not (0 <= index < len(self.files)):
            return
            
        del self.files[index]
        self.update_thumbnails()
        self.status_bar.config(text=f"Datei entfernt  |  {len(self.files)} Datei(en)")
        
        # Aktualisiere Vorschau
        if not self.files:
            self._reset_preview()
        elif index > 0:
            self.show_preview(index - 1)  # Zeige vorheriges Bild
        else:
            self.show_preview(0)  # Zeige erstes Bild

    # ── Thumbnails ─────────────────────────────────────────────────────────────

    def update_thumbnails(self) -> None:
        """Aktualisiert die Thumbnail-Anzeige für alle Dateien."""
        # Lösche alte Thumbnails
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        self.thumbnails = []
        
        # Aktualisiere Statusleiste
        self._update_status_bar()

        # Erstelle Thumbnails für alle Dateien
        for file_index, file_path in enumerate(self.files):
            thumbnail_frame = self._create_thumbnail_widget(file_index, file_path)
            self.thumbnails.append(thumbnail_frame)
    
    def _update_status_bar(self) -> None:
        """Aktualisiert die Statusleiste mit Dateianzahl."""
        pdf_count = sum(1 for f in self.files if f.lower().endswith('.pdf'))
        image_count = len(self.files) - pdf_count
        
        status_text = f"Bereit  |  {len(self.files)} Datei(en)"
        if self.files:
            status_text += f"  ({pdf_count} PDF, {image_count} Bild)"
        
        self.status_bar.config(text=status_text)
    
    def _create_thumbnail_widget(self, file_index: int, file_path: str) -> tk.Frame:
        """Erstellt ein einzelnes Thumbnail-Widget."""
        # Äußerer Frame
        outer_frame = tk.Frame(self.thumb_frame, bg=CLR_BG, cursor="hand2")
        outer_frame.pack(pady=4, padx=6, fill=tk.X)

        # Innerer Frame mit Rahmen
        inner_frame = tk.Frame(outer_frame, bg="white", bd=1, relief=tk.RAISED)
        inner_frame.pack(fill=tk.BOTH, padx=2, pady=1)

        # Thumbnail-Bild
        thumbnail_image = self.create_thumbnail(file_path)
        image_label = tk.Label(inner_frame, image=thumbnail_image, bg="white")
        image_label.image = thumbnail_image  # Referenz behalten
        image_label.pack(side=tk.LEFT, padx=8, pady=5)

        # Dateiname (gekürzt falls zu lang)
        display_name = f"{file_index + 1}. {os.path.basename(file_path)}"
        if len(display_name) > 30:
            display_name = display_name[:27] + "…"
        
        name_label = tk.Label(
            inner_frame,
            text=display_name,
            bg="white",
            anchor="w",
            font=("Arial", 9)
        )
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Löschen-Button
        delete_button = tk.Button(
            inner_frame,
            text="✕",
            command=lambda: self.delete_file(file_index),
            bg=CLR_RED,
            fg="white",
            width=3,
            relief=tk.FLAT,
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        delete_button.pack(side=tk.RIGHT, padx=5)

        # Drag & Drop und Vorschau-Events binden
        for widget in (outer_frame, inner_frame, image_label, name_label):
            widget.bind(
                "<ButtonPress-1>",
                lambda e, idx=file_index, frm=outer_frame: self.on_thumbnail_press(e, idx, frm)
            )
            widget.bind("<B1-Motion>", self.drag_motion)
            widget.bind(
                "<ButtonRelease-1>",
                lambda e, idx=file_index: self.on_thumbnail_release(e, idx)
            )

        return outer_frame

    def create_thumbnail(self, file: str) -> ImageTk.PhotoImage:
        try:
            if file.lower().endswith(".pdf"):
                img = self._render_pdf_page(file, scale=0.3) or _pdf_placeholder()
            else:
                img = Image.open(file)
            img.thumbnail((80, 80))
            return ImageTk.PhotoImage(img)
        except Exception:
            return ImageTk.PhotoImage(_pdf_placeholder())

    def show_preview(self, index: int) -> None:
        """Zeigt eine Vorschau der Datei an der angegebenen Position."""
        try:
            if not (0 <= index < len(self.files)):
                return
            
            file_path = self.files[index]
            print(f"Zeige Vorschau für: {file_path}")  # Debug
            
            # Lade Bild (PDF oder Bilddatei)
            preview_image = self._load_preview_image(file_path)
            if preview_image is None:
                return
            
            # Skaliere Bild für Vorschau
            max_preview_size = 800
            preview_image.thumbnail((max_preview_size, max_preview_size), Image.Resampling.LANCZOS)
            
            # Zeige Vorschau an
            preview_photo = ImageTk.PhotoImage(preview_image)
            self.preview_label.config(image=preview_photo, text="", compound="center")
            self.preview_label.image = preview_photo  # Referenz behalten!
            
            print(f"Vorschau gesetzt: {preview_image.size}")  # Debug
            
        except Exception as exc:
            print(f"Fehler: {exc}")  # Debug
            messagebox.showerror(
                "Vorschau-Fehler",
                f"Datei konnte nicht geladen werden:\n{exc}"
            )
    
    def _load_preview_image(self, file_path: str) -> Image.Image | None:
        """Lädt ein Bild für die Vorschau (PDF oder Bilddatei)."""
        if file_path.lower().endswith(".pdf"):
            preview_image = self._render_pdf_page(file_path, scale=2.0)
            
            if preview_image is None:
                if not HAS_PYMUPDF:
                    pdf_reader = PdfReader(file_path)
                    messagebox.showinfo(
                        "PDF Info",
                        f"Seitenanzahl: {len(pdf_reader.pages)}"
                    )
                else:
                    messagebox.showerror("Fehler", "PDF konnte nicht geladen werden.")
                return None
            
            return preview_image
        else:
            return Image.open(file_path)

    def _render_pdf_page(self, file: str, scale: float = 1.0) -> Image.Image | None:
        """Rendert die erste Seite eines PDFs als Bild (falls PyMuPDF verfügbar)."""
        if not HAS_PYMUPDF:
            return None
        try:
            doc = pymupdf.open(file)
            page = doc[0]
            mat = pymupdf.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            doc.close()
            return img
        except Exception:
            return None

    # ── Drag & Drop (intern) ───────────────────────────────────────────────────

    def _on_mousewheel(self, event) -> None:
        direction = 1 if (event.num == 5 or event.delta < 0) else -1
        self.canvas.yview_scroll(direction, "units")

    def on_thumbnail_press(self, event, index: int, frame: tk.Frame) -> None:
        """Wird beim Drücken auf ein Thumbnail aufgerufen (Start des Drag & Drop)."""
        self.drag_data = {
            "index": index,
            "widget": frame,
            "moved": False
        }
        frame.config(bg=CLR_BLUE)  # Markiere ausgewähltes Thumbnail

    def on_thumbnail_release(self, event, index: int) -> None:
        """Wird beim Loslassen aufgerufen - zeigt Vorschau wenn nicht gedraggt wurde."""
        # Setze Farbe zurück
        if self.drag_data["widget"]:
            self.drag_data["widget"].config(bg=CLR_DARK)
        
        # Zeige Vorschau nur bei Klick (nicht bei Drag)
        was_dragged = self.drag_data.get("moved", False)
        if not was_dragged:
            self.show_preview(index)
        
        # Setze Drag-Daten zurück
        self.drag_data = {"index": None, "widget": None, "moved": False}

    def drag_motion(self, event) -> None:
        """Verarbeitet Drag-Bewegungen zum Umsortieren von Thumbnails."""
        if self.drag_data["index"] is None:
            return
        
        self.drag_data["moved"] = True  # Markiere dass gedraggt wurde
        
        # Finde Ziel-Widget unter Mauszeiger
        pointer_x, pointer_y = event.widget.winfo_pointerxy()
        target_widget = event.widget.winfo_containing(pointer_x, pointer_y)
        
        # Navigiere zum Thumbnail-Frame
        while target_widget and target_widget not in self.thumbnails:
            target_widget = target_widget.master
        
        # Sortiere Dateien um wenn über anderem Thumbnail
        if target_widget and target_widget in self.thumbnails:
            target_index = self.thumbnails.index(target_widget)
            dragged_index = self.drag_data["index"]
            
            if target_index != dragged_index:
                # Verschiebe Datei in Liste
                moved_file = self.files.pop(dragged_index)
                self.files.insert(target_index, moved_file)
                
                # Aktualisiere Drag-Index
                self.drag_data["index"] = target_index
                
                # Aktualisiere UI (behalte Drag-Status)
                was_moved = self.drag_data["moved"]
                self.update_thumbnails()
                self.drag_data["moved"] = was_moved
                self.drag_data["widget"] = self.thumbnails[target_index]
                self.drag_data["widget"].config(bg=CLR_BLUE)

    # ── PDF-Export ─────────────────────────────────────────────────────────────

    def save_pdf(self) -> None:
        """Exportiert alle Dateien als zusammengefügtes PDF."""
        if not self.files:
            messagebox.showwarning("Warnung", "Keine Dateien hinzugefügt.")
            return

        # Speicherort wählen
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF-Dateien", "*.pdf")]
        )
        if not save_path:
            return

        self.status_bar.config(text="Erstelle PDF …")
        self.root.update()

        try:
            pdf_writer = PdfWriter()
            total_files = len(self.files)
            
            # Verarbeite jede Datei
            for file_number, file_path in enumerate(self.files, 1):
                self.status_bar.config(text=f"Verarbeite Datei {file_number}/{total_files} …")
                self.root.update()
                
                if file_path.lower().endswith(".pdf"):
                    self._add_pdf_to_output(file_path, pdf_writer)
                else:
                    self._add_image_to_output(file_path, pdf_writer)

            # Speichere finales PDF
            with open(save_path, "wb") as output_file:
                pdf_writer.write(output_file)

            self.status_bar.config(text=f"Bereit  |  {len(self.files)} Datei(en)")
            messagebox.showinfo(
                "Gespeichert",
                f"PDF erfolgreich gespeichert:\n{save_path}"
            )
        except Exception as exc:
            self.status_bar.config(text=f"Bereit  |  {len(self.files)} Datei(en)")
            messagebox.showerror(
                "Fehler beim Speichern",
                f"PDF konnte nicht erstellt werden:\n{exc}"
            )
    
    def _add_pdf_to_output(self, pdf_path: str, output: PdfWriter) -> None:
        """Fügt alle Seiten eines PDFs zum Output hinzu."""
        pdf_reader = PdfReader(pdf_path)
        for page in pdf_reader.pages:
            output.add_page(page)
    
    def _add_image_to_output(self, image_path: str, output: PdfWriter) -> None:
        """Konvertiert ein Bild zu PDF und fügt es zum Output hinzu."""
        image = Image.open(image_path)
        
        # Konvertiere zu RGB falls nötig
        if image.mode in ("RGBA", "LA", "P"):
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            
            # Füge Bild mit Transparenz ein
            alpha_mask = image.split()[-1] if image.mode in ("RGBA", "LA") else None
            rgb_image.paste(image, mask=alpha_mask)
            image = rgb_image
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # Speichere als temporäres PDF
        temp_pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        image.save(temp_pdf_path, "PDF", resolution=100.0, quality=95)
        
        # Füge zum Output hinzu und lösche temporäre Datei
        output.add_page(PdfReader(temp_pdf_path).pages[0])
        os.unlink(temp_pdf_path)


if __name__ == "__main__":
    try:
        root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
        app = PDFFusionApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        error_msg = f"Ein kritischer Fehler ist aufgetreten:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            messagebox.showerror("Kritischer Fehler", error_msg)
        except:
            print("Fehler beim Anzeigen der Fehlermeldung")
        raise

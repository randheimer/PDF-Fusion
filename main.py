import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk, ImageGrab, ImageDraw
from PyPDF2 import PdfReader, PdfWriter

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

# ── Farb-Konstanten ────────────────────────────────────────────────────────────
CLR_DARK    = "#22303f"
CLR_PANEL   = "#2a3f55"
CLR_LIGHT   = "#f6f9fc"
CLR_BG      = "#e9eff6"
CLR_GREEN   = "#2aa650"
CLR_BLUE    = "#2d8fca"
CLR_RED     = "#d94836"
CLR_ORANGE  = "#e67e22"
CLR_MUTED   = "#5f6b77"

SUPPORTED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png")


def _pdf_placeholder(size: tuple[int, int] = (80, 80)) -> Image.Image:
    """Erstellt ein graues Platzhalterbild für PDFs ohne Vorschau."""
    img = Image.new("RGB", size, "lightgray")
    draw = ImageDraw.Draw(img)
    draw.text((size[0] // 2 - 10, size[1] // 2 - 5), "PDF", fill="black")
    return img


class PDFFusionApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PDF Fusion")
        self.root.geometry("1200x700")
        self.root.minsize(800, 500)
        self.root.configure(bg=CLR_BG)

        self.files: list[str] = []
        self.thumbnails: list[tk.Frame] = []
        self.drag_data: dict = {"index": None, "widget": None}

        if HAS_DND:
            try:
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind("<<Drop>>", self.drop_files)
            except Exception:
                pass

        self._build_ui()

    # ── UI-Aufbau ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.left_frame = tk.Frame(self.root, width=340, bg=CLR_DARK)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(self.root, bg=CLR_LIGHT, padx=12, pady=12)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_sidebar()
        self._build_preview()
        self._build_statusbar()

    def _build_sidebar(self) -> None:
        btn_frame = tk.Frame(self.left_frame, bg=CLR_DARK)
        btn_frame.pack(pady=10, padx=12, fill=tk.X)

        tk.Label(btn_frame, text="PDF Fusion", font=("Segoe UI", 17, "bold"),
                 bg=CLR_DARK, fg="white", pady=6).pack(pady=(0, 18), fill=tk.X)

        buttons = [
            ("➕  Dateien hinzufügen", CLR_GREEN,  ("Segoe UI", 11, "bold"), self.add_files),
            ("📋  Aus Zwischenablage", CLR_BLUE,   ("Segoe UI", 11, "bold"), self.paste_image),
            ("🗑️  Alle löschen",       CLR_RED,    ("Segoe UI", 11, "bold"), self.clear_all),
            ("💾  Als PDF speichern",  CLR_ORANGE, ("Segoe UI", 12, "bold"), self.save_pdf),
        ]
        for i, (text, color, font, cmd) in enumerate(buttons):
            b = tk.Button(btn_frame, text=text, command=cmd,
                          bg=color, fg="white", font=font,
                          relief=tk.FLAT, cursor="hand2", activebackground="white",
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

        # Scrollbarer Thumbnail-Bereich
        container = tk.Frame(self.left_frame, bg=CLR_PANEL)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.canvas = tk.Canvas(container, bg=CLR_PANEL, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
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
            text="Doppelklick auf ein Thumbnail zeigt Vorschau an",
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
        for f in self.root.tk.splitlist(event.data):
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                self.files.append(f)
        self.update_thumbnails()

    def add_files(self) -> None:
        chosen = filedialog.askopenfilenames(
            filetypes=[("Bilder & PDFs", "*.jpg *.jpeg *.png *.pdf"), ("Alle Dateien", "*.*")]
        )
        self.files.extend(chosen)
        self.update_thumbnails()

    def clear_all(self) -> None:
        if self.files and messagebox.askyesno("Bestätigung", "Alle Dateien entfernen?"):
            self.files.clear()
            self.update_thumbnails()
            self.preview_label.config(
                image="",
                text="Ziehe Dateien hierher\noder klicke auf 'Dateien hinzufügen'"
            )

    def paste_image(self) -> None:
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                img.save(tmp)
                self.files.append(tmp)
                self.update_thumbnails()
            else:
                messagebox.showwarning("Einfügen", "Kein Bild in der Zwischenablage gefunden.")
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))

    def delete_file(self, index: int) -> None:
        del self.files[index]
        self.update_thumbnails()

    # ── Thumbnails ─────────────────────────────────────────────────────────────

    def update_thumbnails(self) -> None:
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        self.thumbnails = []
        self.status_bar.config(text=f"Bereit  |  {len(self.files)} Datei(en)")

        for idx, file in enumerate(self.files):
            frame = tk.Frame(self.thumb_frame, bg=CLR_BG, cursor="hand2")
            frame.pack(pady=4, padx=6, fill=tk.X)

            inner = tk.Frame(frame, bg="white", bd=1, relief=tk.RAISED)
            inner.pack(fill=tk.BOTH, padx=2, pady=1)

            thumb_img = self.create_thumbnail(file)
            lbl = tk.Label(inner, image=thumb_img, bg="white")
            lbl.image = thumb_img
            lbl.pack(side=tk.LEFT, padx=8, pady=5)

            name = f"{idx + 1}. {os.path.basename(file)}"
            if len(name) > 30:
                name = name[:27] + "…"
            name_lbl = tk.Label(inner, text=name, bg="white", anchor="w", font=("Arial", 9))
            name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            tk.Button(inner, text="✕", command=lambda i=idx: self.delete_file(i),
                      bg=CLR_RED, fg="white", width=3, relief=tk.FLAT,
                      font=("Arial", 10, "bold"), cursor="hand2").pack(side=tk.RIGHT, padx=5)

            for w in (frame, inner, lbl, name_lbl):
                w.bind("<ButtonPress-1>",   lambda e, i=idx, f=frame: self.drag_start(e, i, f))
                w.bind("<B1-Motion>",        self.drag_motion)
                w.bind("<ButtonRelease-1>",  self.drag_release)
                w.bind("<Double-Button-1>",  lambda e, i=idx: self.show_preview(i))

            self.thumbnails.append(frame)

    def create_thumbnail(self, file: str) -> ImageTk.PhotoImage:
        if file.lower().endswith(".pdf"):
            img = self._render_pdf_page(file, scale=0.3) or _pdf_placeholder()
        else:
            img = Image.open(file)
        img.thumbnail((80, 80))
        return ImageTk.PhotoImage(img)

    def show_preview(self, index: int) -> None:
        file = self.files[index]
        if file.lower().endswith(".pdf"):
            img = self._render_pdf_page(file, scale=1.5)
            if img is None:
                if not HAS_PYMUPDF:
                    pdf = PdfReader(file)
                    messagebox.showinfo("PDF Info", f"Seitenanzahl: {len(pdf.pages)}")
                else:
                    messagebox.showerror("Fehler", "PDF konnte nicht geladen werden.")
                return
        else:
            img = Image.open(file)

        img.thumbnail((600, 600))
        img_tk = ImageTk.PhotoImage(img)
        self.preview_label.config(image=img_tk, text="")
        self.preview_label.image = img_tk

    # ── Drag & Drop (intern) ───────────────────────────────────────────────────

    def _on_mousewheel(self, event) -> None:
        direction = 1 if (event.num == 5 or event.delta < 0) else -1
        self.canvas.yview_scroll(direction, "units")

    def drag_start(self, event, index: int, frame: tk.Frame) -> None:
        self.drag_data = {"index": index, "widget": frame}
        frame.config(bg=CLR_BLUE)

    def drag_motion(self, event) -> None:
        if self.drag_data["index"] is None:
            return
        x, y = event.widget.winfo_pointerxy()
        target = event.widget.winfo_containing(x, y)
        while target and target not in self.thumbnails:
            target = target.master
        if target and target in self.thumbnails:
            target_idx = self.thumbnails.index(target)
            drag_idx   = self.drag_data["index"]
            if target_idx != drag_idx:
                self.files.insert(target_idx, self.files.pop(drag_idx))
                self.drag_data["index"] = target_idx
                self.update_thumbnails()
                self.drag_data["widget"] = self.thumbnails[target_idx]
                self.drag_data["widget"].config(bg=CLR_BLUE)

    def drag_release(self, event) -> None:
        if self.drag_data["widget"]:
            self.drag_data["widget"].config(bg=CLR_DARK)
        self.drag_data = {"index": None, "widget": None}

    # ── PDF-Export ─────────────────────────────────────────────────────────────

    def save_pdf(self) -> None:
        if not self.files:
            messagebox.showwarning("Warnung", "Keine Dateien hinzugefügt.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF-Dateien", "*.pdf")]
        )
        if not save_path:
            return

        self.status_bar.config(text="Erstelle PDF …")
        self.root.update()

        output = PdfWriter()
        for file in self.files:
            if file.lower().endswith(".pdf"):
                for page in PdfReader(file).pages:
                    output.add_page(page)
            else:
                img = Image.open(file)
                if img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = bg
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
                img.save(tmp_pdf, "PDF", resolution=100.0, quality=95)
                output.add_page(PdfReader(tmp_pdf).pages[0])
                os.unlink(tmp_pdf)

        with open(save_path, "wb") as f:
            output.write(f)

        self.status_bar.config(text=f"Bereit  |  {len(self.files)} Datei(en)")
        messagebox.showinfo("Gespeichert", f"PDF erfolgreich gespeichert:\n{save_path}")

    # ── Hilfsmethoden ──────────────────────────────────────────────────────────

    def _render_pdf_page(self, path: str, scale: float = 1.0) -> Image.Image | None:
        """Rendert die erste Seite einer PDF-Datei als PIL-Image. Gibt None zurück bei Fehler."""
        if not HAS_PYMUPDF:
            return None
        try:
            doc = pymupdf.open(path)
            pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(scale, scale))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return img
        except Exception:
            return None


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

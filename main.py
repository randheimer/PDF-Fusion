"""
PDF Fusion - A modern PDF editor for Windows.
Merges PDF files and images into a single PDF document.
"""

import logging
import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk, ImageGrab, ImageDraw
from PyPDF2 import PdfReader

from pdf_fusion.core.formats import SUPPORTED_EXTENSIONS
from pdf_fusion.core.merge import merge_to_pdf

# Check optional dependencies
try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf  # PyMuPDF before 1.24.3 only provides this module name
    except ImportError:
        pymupdf = None
HAS_PYMUPDF = pymupdf is not None

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# Color scheme
CLR_DARK = "#22303f"
CLR_PANEL = "#2a3f55"
CLR_LIGHT = "#f6f9fc"
CLR_BG = "#e9eff6"
CLR_GREEN = "#2aa650"
CLR_BLUE = "#2d8fca"
CLR_RED = "#d94836"
CLR_ORANGE = "#e67e22"
CLR_MUTED = "#5f6b77"


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _placeholder(size: tuple[int, int] = (80, 80), text: str = "PDF") -> Image.Image:
    """
    Creates a gray placeholder image, for example for PDFs without a preview.

    Args:
        size: Tuple of (width, height) of the placeholder image
        text: Label of the placeholder

    Returns:
        PIL Image object with a gray background and the label
    """
    img = Image.new("RGB", size, "lightgray")
    draw = ImageDraw.Draw(img)
    draw.text((size[0] // 2 - 10, size[1] // 2 - 5), text, fill="black")
    return img


# ═══════════════════════════════════════════════════════════════════════════
# MAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════

class PDFFusionApp:
    """
    Main application of PDF Fusion.

    Adds, sorts and merges PDF and image files into a single PDF document
    through a graphical user interface.
    """

    def __init__(self, root: tk.Tk) -> None:
        """
        Initializes the application.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self._setup_window()

        # Data management
        self.files: list[str] = []  # All file paths in the list
        self.thumbnails: list[tk.Frame] = []  # Thumbnail widgets
        self._thumbnail_cache: dict[str, ImageTk.PhotoImage] = {}  # Rendered thumbnails per file path
        self._temp_files: set[str] = set()  # Temp files created by paste_image
        self._preview_path: str | None = None  # Last previewed file
        self._preview_refresh_job: str | None = None  # Pending after() call for re-scaling
        self.drag_data: dict = {  # Drag & drop state
            "index": None,
            "widget": None,
            "moved": False
        }

        self._setup_drag_and_drop()
        self._setup_keyboard_shortcuts()
        self._build_ui()

    def _setup_window(self) -> None:
        """Configures the main window."""
        self.root.title("PDF Fusion")
        self.root.geometry("1200x700")
        self.root.minsize(800, 500)
        self.root.configure(bg=CLR_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_drag_and_drop(self) -> None:
        """Enables drag & drop if it is available."""
        if HAS_DND:
            try:
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind("<<Drop>>", self.drop_files)
            except Exception:
                pass

    def _setup_keyboard_shortcuts(self) -> None:
        """Registers keyboard shortcuts."""
        self.root.bind("<Control-o>", lambda e: self.add_files())
        self.root.bind("<Control-v>", lambda e: self.paste_image())
        self.root.bind("<Control-s>", lambda e: self.save_pdf())
        self.root.bind("<Delete>", lambda e: self.clear_all())

    # ═══════════════════════════════════════════════════════════════════════
    # UI SETUP
    # ═══════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        """Builds the entire user interface."""
        # Pack the status bar first so it spans the full width
        self._build_statusbar()

        # Left sidebar (buttons + thumbnails)
        self.left_frame = tk.Frame(self.root, width=340, bg=CLR_DARK)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.left_frame.pack_propagate(False)

        # Right area (preview)
        self.right_frame = tk.Frame(self.root, bg=CLR_LIGHT, padx=12, pady=12)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_sidebar()
        self._build_preview()

    def _build_sidebar(self) -> None:
        """Builds the left sidebar with buttons and the thumbnail list."""
        btn_frame = tk.Frame(self.left_frame, bg=CLR_DARK)
        btn_frame.pack(pady=10, padx=12, fill=tk.X)

        # Title
        tk.Label(
            btn_frame,
            text="PDF Fusion",
            font=("Segoe UI", 17, "bold"),
            bg=CLR_DARK,
            fg="white",
            pady=6
        ).pack(pady=(0, 18), fill=tk.X)

        # Action buttons
        buttons = [
            ("➕  Add files (Ctrl+O)", CLR_GREEN, ("Segoe UI", 10, "bold"), self.add_files),
            ("📋  Paste from clipboard (Ctrl+V)", CLR_BLUE, ("Segoe UI", 10, "bold"), self.paste_image),
            ("🗑️  Clear all (Delete)", CLR_RED, ("Segoe UI", 10, "bold"), self.clear_all),
            ("💾  Save as PDF (Ctrl+S)", CLR_ORANGE, ("Segoe UI", 11, "bold"), self.save_pdf),
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
                activeforeground="black",
                bd=0)
            b.pack(pady=(10 if i == 0 else 6), fill=tk.X)

        # Scrollable thumbnail area
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
        tk.Label(header, text="Preview", font=("Segoe UI", 13, "bold"),
                 bg=CLR_PANEL, fg="white").pack(pady=12)

        preview_box = tk.Frame(self.right_frame, bg="white", bd=1, relief=tk.SOLID)
        preview_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(10, 8))
        # Do not let the preview image size propagate into the layout; otherwise
        # every preview would move the sidebar and clip the status bar
        preview_box.pack_propagate(False)

        self.preview_label = tk.Label(
            preview_box,
            text="Drop files here\nor click 'Add files'",
            bg="white", fg=CLR_MUTED, font=("Segoe UI", 12), justify=tk.CENTER
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        # Re-scale the preview when the label is resized
        self.preview_label.bind("<Configure>", self._on_preview_resize)

        self.preview_instructions = tk.Label(
            self.right_frame,
            text="Click a thumbnail to preview it • Drag to reorder",
            bg=CLR_LIGHT, fg=CLR_MUTED, font=("Segoe UI", 10, "italic")
        )
        self.preview_instructions.pack(fill=tk.X, pady=(0, 6))

    def _build_statusbar(self) -> None:
        self.status_bar = tk.Label(
            self.root, text="Ready  |  0 files",
            bg=CLR_PANEL, fg="white", anchor="w", padx=14, pady=4,
            font=("Segoe UI", 10)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ── File management ────────────────────────────────────────────────────────

    def drop_files(self, event) -> None:
        """Handles files added by drag & drop."""
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
                text=f"{added_count} file(s) added by drag & drop  |  {total_files} total"
            )

    def add_files(self) -> None:
        """Opens the file dialog and adds the selected files."""
        selected_files = filedialog.askopenfilenames(
            title="Select files",
            filetypes=[
                ("Images & PDFs", "*.jpg *.jpeg *.png *.pdf"),
                ("All files", "*.*")
            ]
        )

        # "All files" also lets unsupported formats through, so filter them here
        supported = [f for f in selected_files if f.lower().endswith(SUPPORTED_EXTENSIONS)]
        rejected = len(selected_files) - len(supported)
        if rejected:
            messagebox.showwarning(
                "Unsupported file",
                f"{rejected} file(s) have an unsupported format and were ignored."
            )

        if supported:
            self.files.extend(supported)
            self.update_thumbnails()
            self.status_bar.config(
                text=f"{len(supported)} file(s) added  |  {len(self.files)} total"
            )

    def clear_all(self) -> None:
        """Removes all files after confirmation."""
        if not self.files:
            return

        if messagebox.askyesno("Confirm", "Remove all files?"):
            for path in self.files:
                self._discard_temp_file(path)
            self.files.clear()
            self.update_thumbnails()
            self._reset_preview()
            self.status_bar.config(text="All files removed  |  0 files")

    def _reset_preview(self) -> None:
        """Resets the preview to its default state."""
        self._preview_path = None
        self.preview_label.config(
            image="",
            text="Drop files here\nor click 'Add files'"
        )

    def paste_image(self) -> None:
        """Adds an image from the clipboard."""
        try:
            clipboard_image = ImageGrab.grabclipboard()

            if isinstance(clipboard_image, Image.Image):
                # Save the image to a temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                clipboard_image.save(temp_file)

                self._temp_files.add(temp_file)
                self.files.append(temp_file)
                self.update_thumbnails()
                self.status_bar.config(
                    text=f"Image pasted from clipboard  |  {len(self.files)} file(s)"
                )
            else:
                messagebox.showwarning(
                    "Paste",
                    "No image found in the clipboard."
                )
        except Exception as exc:
            messagebox.showerror("Error", f"Error while pasting: {exc}")

    def delete_file(self, index: int) -> None:
        """Removes the file at the given position."""
        if not (0 <= index < len(self.files)):
            return

        self._discard_temp_file(self.files.pop(index))
        self.update_thumbnails()
        self.status_bar.config(text=f"File removed  |  {len(self.files)} file(s)")

        # Update the preview
        if not self.files:
            self._reset_preview()
        elif index > 0:
            self.show_preview(index - 1)  # Show the previous image
        else:
            self.show_preview(0)  # Show the first image

    # ── Thumbnails ─────────────────────────────────────────────────────────────

    def _discard_temp_file(self, path: str) -> None:
        """Deletes a temp file created by paste_image once it is no longer in the list."""
        if path in self._temp_files:
            self._temp_files.discard(path)
            if os.path.exists(path):
                os.remove(path)

    def _on_close(self) -> None:
        """Removes the clipboard temp files and closes the window."""
        for path in list(self._temp_files):
            self._discard_temp_file(path)
        self.root.destroy()

    def update_thumbnails(self) -> None:
        """Refreshes the thumbnails for all files."""
        # Remove old thumbnails
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        self.thumbnails = []
        # Drop cache entries for files that are no longer in the list
        self._thumbnail_cache = {
            path: img for path, img in self._thumbnail_cache.items() if path in self.files
        }

        # Update the status bar
        self._update_status_bar()

        # Create thumbnails for all files
        for file_index, file_path in enumerate(self.files):
            thumbnail_frame = self._create_thumbnail_widget(file_index, file_path)
            self.thumbnails.append(thumbnail_frame)

    def _update_status_bar(self) -> None:
        """Updates the status bar with the file count."""
        pdf_count = sum(1 for f in self.files if f.lower().endswith('.pdf'))
        image_count = len(self.files) - pdf_count

        status_text = f"Ready  |  {len(self.files)} file(s)"
        if self.files:
            status_text += f"  ({pdf_count} PDF, {image_count} image(s))"

        self.status_bar.config(text=status_text)

    def _create_thumbnail_widget(self, file_index: int, file_path: str) -> tk.Frame:
        """Creates a single thumbnail widget."""
        # Outer frame
        outer_frame = tk.Frame(self.thumb_frame, bg=CLR_BG, cursor="hand2")
        outer_frame.pack(pady=4, padx=6, fill=tk.X)

        # Inner frame with border
        inner_frame = tk.Frame(outer_frame, bg="white", bd=1, relief=tk.RAISED)
        inner_frame.pack(fill=tk.BOTH, padx=2, pady=1)

        # Thumbnail image
        thumbnail_image = self._get_thumbnail(file_path)
        image_label = tk.Label(inner_frame, image=thumbnail_image, bg="white")
        image_label.image = thumbnail_image  # Keep a reference
        image_label.pack(side=tk.LEFT, padx=8, pady=5)

        # File name (shortened if too long)
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

        # Delete button
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

        # Bind drag & drop and preview events
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

    def _get_thumbnail(self, file_path: str) -> ImageTk.PhotoImage:
        """Returns the thumbnail for a file; each path is rendered only once."""
        if file_path not in self._thumbnail_cache:
            self._thumbnail_cache[file_path] = self.create_thumbnail(file_path)
        return self._thumbnail_cache[file_path]

    def create_thumbnail(self, file: str) -> ImageTk.PhotoImage:
        try:
            if file.lower().endswith(".pdf"):
                img = self._render_pdf_page(file, scale=0.3) or _placeholder()
            else:
                img = Image.open(file)
            img.thumbnail((80, 80))
            return ImageTk.PhotoImage(img)
        except Exception:
            # Unreadable file: use a separate placeholder instead of "PDF" so the error stays visible
            logger.exception("Could not create thumbnail: %s", file)
            return ImageTk.PhotoImage(_placeholder(text="?"))

    def _on_preview_resize(self, event) -> None:
        """Re-scales the preview after a resize, with a short delay."""
        if self._preview_path is None:
            return
        if self._preview_refresh_job is not None:
            self.root.after_cancel(self._preview_refresh_job)
        self._preview_refresh_job = self.root.after(150, self._refresh_preview)

    def _refresh_preview(self) -> None:
        """Redraws the current preview at the new size."""
        self._preview_refresh_job = None
        if self._preview_path in self.files:
            self.show_preview(self.files.index(self._preview_path))

    def show_preview(self, index: int) -> None:
        """Shows a preview of the file at the given position."""
        try:
            if not (0 <= index < len(self.files)):
                return

            file_path = self.files[index]
            self._preview_path = file_path

            # Load the image (PDF or image file)
            preview_image = self._load_preview_image(file_path)
            if preview_image is None:
                return

            # Scale the image to the available space; before the first layout the space is still 1x1
            available = (self.preview_label.winfo_width(), self.preview_label.winfo_height())
            if min(available) < 2:
                available = (800, 800)
            preview_image.thumbnail(available, Image.Resampling.LANCZOS)

            # Show the preview
            preview_photo = ImageTk.PhotoImage(preview_image)
            self.preview_label.config(image=preview_photo, text="", compound="center")
            self.preview_label.image = preview_photo  # Keep a reference!

        except Exception as exc:
            messagebox.showerror(
                "Preview error",
                f"Could not load file:\n{exc}"
            )

    def _load_preview_image(self, file_path: str) -> Image.Image | None:
        """Loads an image for the preview (PDF or image file)."""
        if file_path.lower().endswith(".pdf"):
            preview_image = self._render_pdf_page(file_path, scale=2.0)

            if preview_image is None:
                if not HAS_PYMUPDF:
                    pages = len(PdfReader(file_path).pages)
                    self._show_preview_message(
                        f"PDF preview requires PyMuPDF\nPage count: {pages}"
                    )
                else:
                    self._show_preview_message("Could not load PDF.")
                return None

            return preview_image
        else:
            return Image.open(file_path)

    def _show_preview_message(self, text: str) -> None:
        """Shows a text message in the preview instead of an image."""
        self.preview_label.config(image="", text=text)
        self.preview_label.image = None

    def _render_pdf_page(self, file: str, scale: float = 1.0) -> Image.Image | None:
        """Renders the first page of a PDF as an image (requires PyMuPDF)."""
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
            logger.exception("Could not render PDF: %s", file)
            return None

    # ── Drag & drop (internal) ─────────────────────────────────────────────────

    def _on_mousewheel(self, event) -> None:
        direction = 1 if (event.num == 5 or event.delta < 0) else -1
        self.canvas.yview_scroll(direction, "units")

    def on_thumbnail_press(self, event, index: int, frame: tk.Frame) -> None:
        """Called when a thumbnail is pressed (start of drag & drop)."""
        self.drag_data = {
            "index": index,
            "widget": frame,
            "moved": False
        }
        frame.config(bg=CLR_BLUE)  # Highlight the selected thumbnail

    def on_thumbnail_release(self, event, index: int) -> None:
        """Called on release. Shows the preview if the thumbnail was not dragged."""
        # Reset the color
        if self.drag_data["widget"]:
            self.drag_data["widget"].config(bg=CLR_BG)

        # Only show the preview for a click, not for a drag
        was_dragged = self.drag_data.get("moved", False)
        if not was_dragged:
            self.show_preview(index)

        # Reset the drag state
        self.drag_data = {"index": None, "widget": None, "moved": False}

    def drag_motion(self, event) -> None:
        """Handles drag movements to reorder thumbnails."""
        if self.drag_data["index"] is None:
            return

        self.drag_data["moved"] = True  # Mark that a drag happened

        # Find the widget under the mouse pointer
        pointer_x, pointer_y = event.widget.winfo_pointerxy()
        target_widget = event.widget.winfo_containing(pointer_x, pointer_y)

        # Walk up to the thumbnail frame
        while target_widget and target_widget not in self.thumbnails:
            target_widget = target_widget.master

        # Reorder files when the pointer is over another thumbnail
        if target_widget and target_widget in self.thumbnails:
            target_index = self.thumbnails.index(target_widget)
            dragged_index = self.drag_data["index"]

            if target_index != dragged_index:
                # Move the file in the list
                moved_file = self.files.pop(dragged_index)
                self.files.insert(target_index, moved_file)

                # Update the drag index
                self.drag_data["index"] = target_index

                # Refresh the UI (keep the drag state)
                was_moved = self.drag_data["moved"]
                self.update_thumbnails()
                self.drag_data["moved"] = was_moved
                self.drag_data["widget"] = self.thumbnails[target_index]
                self.drag_data["widget"].config(bg=CLR_BLUE)

    # ── PDF export ─────────────────────────────────────────────────────────────

    def save_pdf(self) -> None:
        """Exports all files as one merged PDF."""
        if not self.files:
            messagebox.showwarning("Warning", "No files added.")
            return

        # Choose the output location
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not save_path:
            return

        self.status_bar.config(text="Creating PDF …")
        # update_idletasks() only redraws. With update(), clicks during the export would
        # be processed and change the file list in the middle of the loop.
        self.root.update_idletasks()

        try:
            merge_to_pdf(self.files, save_path, progress=self._report_progress)

            self.status_bar.config(text=f"Ready  |  {len(self.files)} file(s)")
            messagebox.showinfo(
                "Saved",
                f"PDF saved successfully:\n{save_path}"
            )
        except Exception as exc:
            self.status_bar.config(text=f"Ready  |  {len(self.files)} file(s)")
            messagebox.showerror(
                "Save error",
                f"Could not create PDF:\n{exc}"
            )

    def _report_progress(self, number: int, total: int) -> None:
        """Shows the progress of the export in the status bar."""
        self.status_bar.config(text=f"Processing file {number}/{total} …")
        self.root.update_idletasks()


if __name__ == "__main__":
    try:
        root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
        app = PDFFusionApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        error_msg = f"A critical error occurred:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            messagebox.showerror("Critical error", error_msg)
        except:
            print("Could not show the error message")
        raise

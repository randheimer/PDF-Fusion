"""The main application: file list, preview and PDF export, built with CustomTkinter."""

import logging
import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageGrab, ImageTk
from pypdf import PdfReader

from pdf_fusion.core.formats import SUPPORTED_EXTENSIONS
from pdf_fusion.core.merge import MergeError, merge_to_pdf
from pdf_fusion.core.render import HAS_PYMUPDF, render_pdf_page
from pdf_fusion.i18n import t
from pdf_fusion.ui.theme import PALETTE, hover_color
from pdf_fusion.ui.thumbnails import make_thumbnail
from pdf_fusion.ui.window import HAS_DND

if HAS_DND:
    from tkinterdnd2 import DND_FILES

FONT = "Segoe UI"
FALLBACK_PREVIEW_SIZE = (800, 800)
RESIZE_DELAY_MS = 150

logger = logging.getLogger(__name__)


def describe_error(exc: Exception) -> str:
    """Returns the translated text for an export error."""
    if isinstance(exc, MergeError):
        return t("error.process_file", name=exc.file_name, cause=exc.cause)
    return str(exc)


class PDFFusionApp:
    """The file list, the preview and the export of PDF Fusion."""

    def __init__(self, root: ctk.CTk) -> None:
        """
        Builds the application in the given window.

        Args:
            root: The main window, see pdf_fusion.ui.window
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
        self._preview_photo: ctk.CTkImage | None = None  # Image currently shown in the preview
        self._preview_size: tuple[int, int] = (0, 0)  # Size of the shown preview image
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
        ctk.set_appearance_mode("light")  # every color is set explicitly, see ui/theme.py
        self.root.title("PDF Fusion")
        self.root.geometry("1200x700")
        self.root.minsize(800, 500)
        self.root.configure(fg_color=PALETTE["window_bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Configure>", self._on_window_resize, add="+")

    def _setup_drag_and_drop(self) -> None:
        """Enables drag & drop if tkinterdnd2 is available."""
        if HAS_DND:
            try:
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind("<<Drop>>", self.drop_files)
            except Exception:
                logger.exception("Drag & drop could not be enabled")

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
        self.left_frame = ctk.CTkFrame(self.root, width=340, corner_radius=0, fg_color=PALETTE["sidebar"])
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.left_frame.pack_propagate(False)

        # Right area (preview)
        self.right_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color=PALETTE["preview_bg"])
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_sidebar()
        self._build_preview()

    def _build_sidebar(self) -> None:
        """Builds the left sidebar with buttons and the thumbnail list."""
        btn_frame = ctk.CTkFrame(self.left_frame, corner_radius=0, fg_color=PALETTE["sidebar"])
        btn_frame.pack(pady=10, padx=12, fill=tk.X)

        # Title
        ctk.CTkLabel(
            btn_frame,
            text="PDF Fusion",
            font=(FONT, 17, "bold"),
            text_color=PALETTE["white"],
            fg_color=PALETTE["sidebar"],
        ).pack(pady=(6, 24), fill=tk.X)

        # Action buttons
        buttons = [
            (t("button.add_files"), PALETTE["green"], 10, self.add_files),
            (t("button.paste"), PALETTE["blue"], 10, self.paste_image),
            (t("button.clear_all"), PALETTE["red"], 10, self.clear_all),
            (t("button.save_pdf"), PALETTE["orange"], 11, self.save_pdf),
        ]
        for i, (text, color, size, command) in enumerate(buttons):
            ctk.CTkButton(
                btn_frame,
                text=text,
                command=command,
                fg_color=color,
                hover_color=hover_color(color),
                text_color=PALETTE["white"],
                font=(FONT, size, "bold"),
                corner_radius=0,
                height=34,
            ).pack(pady=(10 if i == 0 else 6), fill=tk.X)

        # Scrollable thumbnail area. Its children are the thumbnails, so update_thumbnails()
        # can clear it with winfo_children().
        self.thumb_frame = ctk.CTkScrollableFrame(self.left_frame, corner_radius=0, fg_color=PALETTE["panel"])
        self.thumb_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 12))

    def _build_preview(self) -> None:
        """Builds the preview panel on the right."""
        header = ctk.CTkFrame(self.right_frame, height=50, corner_radius=0, fg_color=PALETTE["panel"])
        header.pack(fill=tk.X, padx=12, pady=(12, 0))
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=t("preview.title"),
            font=(FONT, 13, "bold"),
            text_color=PALETTE["white"],
            fg_color=PALETTE["panel"],
        ).pack(expand=True)

        # Keep the preview image from changing the size of the panel
        preview_box = ctk.CTkFrame(
            self.right_frame,
            corner_radius=0,
            fg_color=PALETTE["white"],
            border_width=1,
            border_color=PALETTE["black"],
        )
        preview_box.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 8))
        preview_box.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(
            preview_box,
            text=t("preview.empty"),
            text_color=PALETTE["muted"],
            fg_color=PALETTE["white"],
            font=(FONT, 12),
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.right_frame,
            text=t("preview.hint"),
            text_color=PALETTE["muted"],
            fg_color=PALETTE["preview_bg"],
            font=(FONT, 10, "italic"),
        ).pack(fill=tk.X, padx=12, pady=(0, 18))

    def _build_statusbar(self) -> None:
        """Builds the status bar at the bottom of the window."""
        bar = ctk.CTkFrame(self.root, height=28, corner_radius=0, fg_color=PALETTE["panel"])
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        bar.pack_propagate(False)
        self.status_bar = ctk.CTkLabel(
            bar,
            text=t("status.ready", count=0),
            text_color=PALETTE["white"],
            fg_color=PALETTE["panel"],
            anchor="w",
            font=(FONT, 10),
        )
        self.status_bar.pack(fill=tk.X, padx=14)

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
            self.status_bar.configure(
                text=t("status.dropped", count=added_count, total=total_files)
            )

    def add_files(self) -> None:
        """Opens the file dialog and adds the selected files."""
        selected_files = filedialog.askopenfilenames(
            title=t("dialog.select_files"),
            filetypes=[
                (t("filetype.images_pdfs"), "*.jpg *.jpeg *.png *.pdf"),
                (t("filetype.all_files"), "*.*")
            ]
        )

        # "All files" also lets unsupported formats through, so filter them here
        supported = [f for f in selected_files if f.lower().endswith(SUPPORTED_EXTENSIONS)]
        rejected = len(selected_files) - len(supported)
        if rejected:
            messagebox.showwarning(
                t("dialog.unsupported"),
                t("warning.unsupported", count=rejected)
            )

        if supported:
            self.files.extend(supported)
            self.update_thumbnails()
            self.status_bar.configure(
                text=t("status.added", count=len(supported), total=len(self.files))
            )

    def clear_all(self) -> None:
        """Removes all files after confirmation."""
        if not self.files:
            return

        if messagebox.askyesno(t("dialog.confirm"), t("dialog.remove_all_question")):
            for path in self.files:
                self._discard_temp_file(path)
            self.files.clear()
            self.update_thumbnails()
            self._reset_preview()
            self.status_bar.configure(text=t("status.cleared"))

    def _reset_preview(self) -> None:
        """Resets the preview to its default state."""
        self._preview_path = None
        self._show_preview_message(t("preview.empty"))

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
                self.status_bar.configure(
                    text=t("status.pasted", total=len(self.files))
                )
            else:
                messagebox.showwarning(
                    t("dialog.paste"),
                    t("warning.no_clipboard_image")
                )
        except Exception as exc:
            messagebox.showerror(t("dialog.error"), t("error.paste", error=exc))

    def delete_file(self, index: int) -> None:
        """Removes the file at the given position."""
        if not (0 <= index < len(self.files)):
            return

        self._discard_temp_file(self.files.pop(index))
        self.update_thumbnails()
        self.status_bar.configure(text=t("status.removed", total=len(self.files)))

        # Update the preview
        if not self.files:
            self._reset_preview()
        elif index > 0:
            self.show_preview(index - 1)  # Show the previous image
        else:
            self.show_preview(0)  # Show the first image

    # ── Temp files and window ──────────────────────────────────────────────────

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

    # ── Thumbnails ─────────────────────────────────────────────────────────────

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

        status_text = t("status.ready", count=len(self.files))
        if self.files:
            status_text += "  " + t("status.breakdown", pdf=pdf_count, images=image_count)

        self.status_bar.configure(text=status_text)

    def _create_thumbnail_widget(self, file_index: int, file_path: str) -> tk.Frame:
        """Creates a single thumbnail widget."""
        # Outer frame
        outer_frame = tk.Frame(self.thumb_frame, bg=PALETTE["window_bg"], cursor="hand2")
        outer_frame.pack(pady=4, padx=6, fill=tk.X)

        # Inner frame with border
        inner_frame = tk.Frame(outer_frame, bg=PALETTE["white"], bd=1, relief=tk.RAISED)
        inner_frame.pack(fill=tk.BOTH, padx=2, pady=1)

        # Thumbnail image
        thumbnail_image = self._get_thumbnail(file_path)
        image_label = tk.Label(inner_frame, image=thumbnail_image, bg=PALETTE["white"])
        image_label.image = thumbnail_image  # Keep a reference
        image_label.pack(side=tk.LEFT, padx=8, pady=5)

        # File name (shortened if too long)
        display_name = f"{file_index + 1}. {os.path.basename(file_path)}"
        if len(display_name) > 30:
            display_name = display_name[:27] + "…"

        name_label = tk.Label(
            inner_frame,
            text=display_name,
            bg=PALETTE["white"],
            anchor="w",
            font=("Arial", 9)
        )
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Delete button
        delete_button = tk.Button(
            inner_frame,
            text="✕",
            command=lambda: self.delete_file(file_index),
            bg=PALETTE["red"],
            fg=PALETTE["white"],
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
            self._thumbnail_cache[file_path] = ImageTk.PhotoImage(make_thumbnail(file_path))
        return self._thumbnail_cache[file_path]

    # ── Preview ────────────────────────────────────────────────────────────────

    def _on_window_resize(self, event) -> None:
        """Re-scales the preview after the window was resized."""
        if event.widget is not self.root:
            return  # Configure events of child widgets also reach the root's bindings
        if self._preview_path is None:
            return
        if self._preview_refresh_job is not None:
            self.root.after_cancel(self._preview_refresh_job)
        self._preview_refresh_job = self.root.after(RESIZE_DELAY_MS, self._refresh_preview)

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

            # Scale the image to the space the preview label has; before the first layout it is still 1x1
            available = (self.preview_label.winfo_width(), self.preview_label.winfo_height())
            if min(available) < 2:
                available = FALLBACK_PREVIEW_SIZE
            preview_image.thumbnail(available, Image.Resampling.LANCZOS)

            self._show_image(preview_image)

        except Exception as exc:
            messagebox.showerror(
                t("dialog.preview_error"),
                t("error.load_file", error=exc)
            )

    def _show_image(self, image: Image.Image) -> None:
        """Shows an image in the preview."""
        self._preview_size = image.size
        self._preview_photo = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
        self.preview_label.configure(image=self._preview_photo, text="")

    def _load_preview_image(self, file_path: str) -> Image.Image | None:
        """Loads an image for the preview (PDF or image file)."""
        if file_path.lower().endswith(".pdf"):
            preview_image = render_pdf_page(file_path, scale=2.0)

            if preview_image is None:
                if not HAS_PYMUPDF:
                    pages = len(PdfReader(file_path).pages)
                    self._show_preview_message(
                        t("preview.needs_pymupdf", pages=pages)
                    )
                else:
                    self._show_preview_message(t("preview.load_failed"))
                return None

            return preview_image
        else:
            return Image.open(file_path)

    def _show_preview_message(self, text: str) -> None:
        """Shows a text message in the preview instead of an image."""
        self._preview_photo = None
        self._preview_size = (0, 0)
        self.preview_label.configure(image="", text=text)

    # ── Drag & drop (internal) ─────────────────────────────────────────────────

    def on_thumbnail_press(self, event, index: int, frame: tk.Frame) -> None:
        """Called when a thumbnail is pressed (start of drag & drop)."""
        self.drag_data = {
            "index": index,
            "widget": frame,
            "moved": False
        }
        frame.config(bg=PALETTE["blue"])  # Highlight the selected thumbnail

    def on_thumbnail_release(self, event, index: int) -> None:
        """Called on release. Shows the preview if the thumbnail was not dragged."""
        # Reset the color
        if self.drag_data["widget"]:
            self.drag_data["widget"].config(bg=PALETTE["window_bg"])

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
                self.drag_data["widget"].config(bg=PALETTE["blue"])

    # ── PDF export ─────────────────────────────────────────────────────────────

    def save_pdf(self) -> None:
        """Exports all files as one merged PDF."""
        if not self.files:
            messagebox.showwarning(t("dialog.warning"), t("warning.no_files"))
            return

        # Choose the output location
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[(t("filetype.pdf"), "*.pdf")]
        )
        if not save_path:
            return

        self.status_bar.configure(text=t("status.creating_pdf"))
        # update_idletasks() only redraws. With update(), clicks during the export would
        # be processed and change the file list in the middle of the loop.
        self.root.update_idletasks()

        try:
            merge_to_pdf(self.files, save_path, progress=self._report_progress)

            self.status_bar.configure(text=t("status.ready", count=len(self.files)))
            messagebox.showinfo(
                t("dialog.saved"),
                t("info.saved", path=save_path)
            )
        except Exception as exc:
            self.status_bar.configure(text=t("status.ready", count=len(self.files)))
            messagebox.showerror(
                t("dialog.save_error"),
                t("error.create_pdf", error=describe_error(exc))
            )

    def _report_progress(self, number: int, total: int) -> None:
        """Shows the progress of the export in the status bar."""
        self.status_bar.configure(text=t("status.processing", number=number, total=total))
        self.root.update_idletasks()

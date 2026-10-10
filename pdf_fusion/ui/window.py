"""The main window: a CustomTkinter window, with tkinterdnd2 drag & drop when it is installed."""

import customtkinter as ctk

try:
    from tkinterdnd2 import TkinterDnD

    HAS_DND = True
except ImportError:
    HAS_DND = False


if HAS_DND:
    class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        """CustomTkinter window that accepts files dropped from the file manager."""

        def __init__(self) -> None:
            super().__init__()
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class MainWindow(ctk.CTk):
        """CustomTkinter window. Drag & drop is not available without tkinterdnd2."""

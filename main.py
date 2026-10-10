"""PDF Fusion entry point. Start the application with `python main.py`."""

import traceback
from tkinter import messagebox

from pdf_fusion.i18n import set_language, t
from pdf_fusion.settings import get_language
from pdf_fusion.ui.app import PDFFusionApp
from pdf_fusion.ui.window import MainWindow


def main() -> None:
    """Creates the window and runs the application until the window is closed."""
    set_language(get_language())
    root = MainWindow()
    PDFFusionApp(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        error_msg = t("error.critical", error=str(exc), trace=traceback.format_exc())
        print(error_msg)
        try:
            messagebox.showerror(t("dialog.critical"), error_msg)
        except Exception:
            print("Could not show the error message")
        raise

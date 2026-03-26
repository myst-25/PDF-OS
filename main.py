"""
PDFOS — PDF - OS (Open Source) v1.2
Entry point.
"""
import sys
import os
import gc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    gc.enable()
    gc.set_threshold(700, 10, 10)
    try:
        from ui.app import run
        run()
    except Exception as e:
        print(f"Fatal: {e}")
        raise
    finally:
        gc.collect()


if __name__ == "__main__":
    main()

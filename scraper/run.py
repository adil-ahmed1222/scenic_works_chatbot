"""CLI entrypoint: python -m scraper.run [--full]"""

from __future__ import annotations

from scraper.crawler import main

if __name__ == "__main__":
    main()

import json
import logging
from pathlib import Path
from config import config
from playwright.sync_api import sync_playwright

# ========= Configuration =========

BASE_DIR = Path(__file__).parent.resolve()
STATE_FILE = BASE_DIR / "latest.json"
BROWSER_PROFILE_DIR = BASE_DIR / "browser_profile"

INTERVAL_SECONDS = ... #TODO: определять в цикле
# =================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def write_state(data: dict):
    tmp_file = STATE_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp_file.replace(STATE_FILE)


def main():
    if not config.ICAN_MAIL or not config.ICAN_PASSWORD:
        logger.error('Не найдены ICAN_MAIL или ICAN_PASSWORD в ".env"')
        return

    BROWSER_PROFILE_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(BROWSER_PROFILE_DIR),
            headless=config.HEADLESS,
        )
        page = context.pages[0] if context.pages else context.new_page()

        logger.info(f"Запуск скрапера. Файл: {STATE_FILE}")
        
        # TODO: Здесь будет цикл опроса и логика логина/чтения


        context.close()


if __name__ == "__main__":
    main()
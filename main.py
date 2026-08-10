import json
import random
import sys
import time
from pathlib import Path

from loguru import logger
from playwright.sync_api import sync_playwright

from config import config

# ========= Configuration =========

BASE_DIR = Path(__file__).parent.resolve()
STATE_FILE = BASE_DIR / "latest.json"
BROWSER_PROFILE_DIR = BASE_DIR / "browser_profile"
LOG_FILE = BASE_DIR / "scraping.log"

# ============ Logger =============

logger.remove()

logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

logger.add(
    LOG_FILE,
    rotation="2MB",
    retention="7 days",
    compression="zip",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)



def write_state(data: dict):
    tmp_file = STATE_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_file.replace(STATE_FILE)


def is_logged_in(page) -> bool:
    try:
        page.wait_for_selector(config.SEL_LOGGED_IN_MARKER, timeout=3000)
        return True
    except Exception:
        return False


def login(page):
    logger.info("[*] Логинимся")
    page.goto(config.LOGIN_URL)
    page.fill(config.SEL_LOGIN_INPUT, config.ICAN_MAIL)
    page.fill(config.SEL_PASS_INPUT, config.ICAN_PASSWORD)
    page.click(config.SEL_SUBMIT_BTN)
    page.wait_for_selector(config.SEL_LOGGED_IN_MARKER, timeout=15000)
    logger.info("[+] Вход выполнен")


def read_reading(page) -> dict:
    page.goto(config.DEVICE_PAGE_URL)
    page.wait_for_selector(config.SEL_VALUE, timeout=15000)

    value = page.text_content(config.SEL_VALUE)
    unit = page.text_content(config.SEL_UNIT) if config.SEL_UNIT else None
    timestamp = page.text_content(config.SEL_TIME) if config.SEL_TIME else None

    return {
        "value": value.strip() if value else None,
        "unit": unit.strip() if unit else None,
        "time": timestamp.strip() if timestamp else None,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }



def main():
    if not config.ICAN_MAIL or not config.ICAN_PASSWORD:
        logger.error('[X] Не найдены ICAN_MAIL или ICAN_PASSWORD в ".env"')
        return

    BROWSER_PROFILE_DIR.mkdir(exist_ok=True)

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(BROWSER_PROFILE_DIR),
            headless=config.HEADLESS,
        )
        page = context.pages[0] if context.pages else context.new_page()

        logger.info(f"[>] Парсер запущен. Файл: {STATE_FILE}")
        
        page.goto(config.DEVICE_PAGE_URL)
        if not is_logged_in(page):
            login(page)
        
        
        logger.info("[+] Вход выполнен, начата проверка")
        
        while True:
            try:
                data = read_reading(page)
                write_state(data)
                logger.info(f"[i] {data['value']} {data['unit']}")
            except Exception as e:
                logger.warning(f"[X] Ошибка: {e}")
                if not is_logged_in(page):
                    try:
                        login(page)
                    except Exception as e2:
                        logger.warning(f"[X] Не удалось перелогиниться: {e2}")
            
            sleep_time = random.randint(config.MIN_SECONDS_INTERVAL, config.MAX_SECONDS_INTERVAL)
            time.sleep(sleep_time)            
                            


if __name__ == "__main__":
    main()
import json
import random
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger
from playwright.sync_api import TimeoutError, sync_playwright

from config import config

BASE_DIR = Path(__file__).parent.resolve()
STATE_FILE = BASE_DIR / "data" / "latest.json"
BROWSER_PROFILE_DIR = BASE_DIR / "data" / "browser_profile"
LOG_FILE = BASE_DIR / "data" / "scraping.log"

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


def _request_shutdown(*_):
    raise KeyboardInterrupt


def write_state(data: dict):
    tmp_file = STATE_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_file.replace(STATE_FILE)


def on_login_page(page) -> bool:
    if page.locator(config.SEL_LOGIN_INPUT).count() > 0:
        return True
    if config.SEL_LOGGED_IN_MARKER:
        return page.locator(config.SEL_LOGGED_IN_MARKER).count() == 0
    return False


def login(page):
    logger.info("[*] Логинимся")
    page.goto(config.LOGIN_URL)
    page.fill(config.SEL_LOGIN_INPUT, config.ICAN_MAIL)
    page.fill(config.SEL_PASS_INPUT, config.ICAN_PASSWORD)
    page.click(config.SEL_SUBMIT_BTN)
    page.wait_for_selector(config.SEL_LOGGED_IN_MARKER, timeout=20000)
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
        "fetched_at": datetime.now(tz=datetime.now().astimezone().tzinfo).strftime("%Y-%m-%d %H:%M:%S"),
    }


def main():
    signal.signal(signal.SIGTERM, _request_shutdown)

    BROWSER_PROFILE_DIR.mkdir(exist_ok=True)

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(BROWSER_PROFILE_DIR),
            headless=config.HEADLESS,
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()

            logger.info(f"[>] Парсер запущен. Файл: {STATE_FILE}")

            page.goto(config.DEVICE_PAGE_URL)
            if on_login_page(page):
                login(page)

            logger.info("[+] Вход выполнен, начата проверка")

            consecutive_failures = 0
            while True:
                try:
                    data = read_reading(page)
                    write_state(data)
                    logger.info(f"[i] {data['value']} {data['unit']}")
                    consecutive_failures = 0
                except TimeoutError as e:
                    consecutive_failures += 1
                    logger.warning(f"[X] Таймаут: {e}")
                    if on_login_page(page) or consecutive_failures >= 3:
                        try:
                            login(page)
                            consecutive_failures = 0
                        except Exception as e2: # noqa: BLE001 - парсер должен продолжить работу
                            logger.warning(f"[X] Не удалось перелогиниться: {e2}")
                except Exception as e: # noqa: BLE001 - ловим всё чтобы не упасть
                    logger.warning(f"[X] Ошибка: {e}")

                sleep_time = random.randint(config.MIN_SECONDS_INTERVAL, config.MAX_SECONDS_INTERVAL)
                time.sleep(sleep_time)
        finally:
            context.close()


if __name__ == "__main__":
    main()

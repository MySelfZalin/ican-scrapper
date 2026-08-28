from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    ICAN_MAIL: str
    ICAN_PASSWORD: str
    MIN_SECONDS_INTERVAL: int
    MAX_SECONDS_INTERVAL: int
    HEADLESS: bool

    LOGIN_URL: str = "https://rus.icancgm.com/review/login?redirect=https://rus.icancgm.com/review/"
    DEVICE_PAGE_URL: str = "https://rus.icancgm.com/review/workbench"
    SEL_LOGIN_INPUT: str = "input[name='account']"
    SEL_PASS_INPUT: str = "input[name='password']"
    SEL_SUBMIT_BTN: str = "button:has-text('Login')"
    SEL_LOGGED_IN_MARKER: str = ".layout-team"
    SEL_VALUE: str = "span.text-\\[36px\\]"
    SEL_UNIT: str = "span.text-\\[14px\\]:has-text('mmol/L')"
    SEL_TIME: str = "p.whitespace-nowrap.text-\\[14px\\]"


config = Config()
from selenium.webdriver.chrome.options import Options


def set_options() -> Options:
    """
    Sets up and returns browser options for the Selenium WebDriver.

    This function configures various options to optimize browser behavior,
    including window maximization, disabling automation features, and setting
    a custom user agent string.

    Returns:
        Options: A configured Options object with the specified settings.
    """
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

    options = Options()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("--ignore-certificate-errors")
    # options.add_argument("--ignore-ssl-errors")
    # options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("detach", True)

    return options

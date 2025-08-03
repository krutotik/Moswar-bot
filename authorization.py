import pickle
from datetime import datetime
from pathlib import Path

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from utils.custom_logging import logger
from utils.human_simulation import random_delay


# Function to login to the game
def log_in(
    driver: WebDriver,
    credentials: dict[str, str],
    cookies_file_path: str = "./cookies/cookies.pkl",
) -> WebDriver:
    """
    Logs in to the Moswar game using either a saved session (from cookies) or
    by submitting login credentials.

    This function first checks if there is a valid cookie file available. If the cookie
    file exists and the session is still valid, it will restore the session using the
    cookies. If the cookie file does not exist or the session is expired, it will
    login with the provided credentials and save the new session cookies.

    Parameters:
        driver (WebDriver): The Selenium WebDriver instance to interact with the browser.
        credentials (dict): A dictionary containing login credentials with keys "login" and "password".
        cookies_file_path (str): The path to the cookie file. Default is "./cookies/cookies.pkl".

    Returns:
        WebDriver: The updated WebDriver instance after successful login.
    """
    logger.info("Logging in to the game.")
    driver.get("https://www.moswar.ru/")

    # Check if cookies file is expired
    cookies_path = Path(cookies_file_path)
    cookies_folder = cookies_path.parent
    is_expired = True

    if cookies_path.exists():
        logger.info("Cookies file found, checking if session is expired")
        with cookies_path.open("rb") as file:
            cookies = pickle.load(file)

        for cookie in cookies:
            if cookie["name"] == "authkey":
                auth_cookie = cookie
                break

        current_time = datetime.timestamp(datetime.now())
        if auth_cookie["expiry"] < current_time:
            logger.warning("Session is expired, deleting cookies file")
            cookies_path.unlink()
        else:
            logger.info("Session is not expired, cookies file is valid")
            is_expired = False

    # Login logic, depending on the session status
    if not is_expired:
        logger.info("Loading session from cookies file")
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
    else:
        logger.info(
            "Cookies file not found or session is expired, creating new session"
        )
        cookies_folder.mkdir(parents=True, exist_ok=True)

        # Login
        login_el = driver.find_element(By.NAME, "email")
        login_el.clear()
        login_el.send_keys(credentials["login"])
        random_delay()

        # Password
        password_el = driver.find_element(By.NAME, "password")
        password_el.clear()
        password_el.send_keys(credentials["password"])
        random_delay()

        # Enter
        enter_el = driver.find_element(
            By.CSS_SELECTOR, 'input[type="submit"][value="Войти"]'
        )
        enter_el.click()
        random_delay()

        # Save cookies
        logger.info("Saving cookies")
        cookies = driver.get_cookies()
        with cookies_path.open("wb") as file:
            pickle.dump(cookies, file)

    return driver

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from entities.player import Player
from utils.custom_logging import logger
from utils.human_simulation import random_delay

# TODO:
# update description and docstrings
# add grab rat tail in metro
# add check rat slots status check for a player


class Metro:
    """
    Represents the 'Metro' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the Metro page.
    """

    BASE_URL = "https://www.moswar.ru/metro/"

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Metro class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def open(self) -> None:
        """
        This method ensures the driver is on the metro page by navigating to its URL.
        """
        if self.driver.current_url != self.BASE_URL:
            logger.info("Driver is not on the metro page. Going to the metro.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the metro page, refreshing.")
            self.driver.refresh()
            random_delay()

    # TODO:
    # 1. for levels with group fights do not return to metro page
    # 2. add check health status
    # 3. add check enemy stats before the attack
    # 4. implement group fights
    # 5. implement events like "new year" to farm better rewards for  levels > 15
    # 6. check the level of underground
    # 8. add swap rat if reward is not good enough
    # 9. add eat snickers if need rest
    def fight_rat(self) -> None:
        """
        TBA
        """
        logger.info("Fighting rat.")
        self.open()

        # Find rat and attack
        logger.info("Finding a rat to attack.")
        try:
            find_rat_el = self.driver.find_element(
                By.XPATH, '//*[@onclick="metroTrackRat();"]'
            )
            find_rat_el.click()
            random_delay()
        except WebDriverException:
            logger.error("Can't start search for rat, player is on rest.")
            return None

        attach_rat_el = self.driver.find_element(
            By.XPATH, '//*[@onclick="metroFightRat();"]'
        )
        logger.info("Rat found. Clicking to attack the rat.")
        attach_rat_el.click()
        random_delay()

        # Return to metro page
        self.driver.get(self.BASE_URL)
        random_delay()
        logger.info("Finished fighting rat.")
        return None

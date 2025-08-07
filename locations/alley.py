import re
from math import e
from typing import Optional

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from entities.player import Player
from schemas.alley import EnemySearchType, ResetTimerType
from utils.custom_logging import logger
from utils.human_simulation import random_delay

# TODO:
# update description and docstrings
# move adresses of buttons to dict at the top of the file


class Alley:
    """
    Represents the 'Alley' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the Alley page.
    """

    BASE_URL = "https://www.moswar.ru/alley/"

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Alley class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def open(self) -> None:
        """
        This method ensures the driver is on the alley page by navigating to its URL.
        """
        if self.driver.current_url != self.BASE_URL:
            logger.info("Driver is not on the alley page. Going to the alley.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the alley page, refreshing.")
            self.driver.refresh()
            random_delay()

    # TIMERS
    # TODO: fix function
    def if_rest_timer(self) -> bool:
        """
        Checks if the player is currently resting based on the rest timer.
        """
        try:
            timer_value = self.driver.find_element(By.CLASS_NAME, "timer").get_attribute("timer")
            if timer_value and "-" not in timer_value:
                logger.info("Player is currently resting.")
                return True
            else:
                return False
        except NoSuchElementException:
            return False

    def reset_timer(self, reset_timer_type: ResetTimerType) -> None:
        """
        Resets the rest timer by consuming a sneaker.
        """
        if not self.if_rest_timer():
            logger.info("Player is not resting, no need to reset the timer.")
            return None

        if reset_timer_type == reset_timer_type.ENERGY:
            logger.info("Resetting energy timer by using enegry.")
            self.driver.find_element(By.XPATH, "//div[@onclick=\"cooldownReset('tonus');\"]").click()
            random_delay()
        elif reset_timer_type == reset_timer_type.SNICKERS:
            logger.info("Resetting rest timer by using sneakers.")

            if self.player.snickers == 0:
                logger.error("Player has no sneakers to reset the timer.")
                return None

            self.driver.find_element(By.XPATH, "//div[@onclick=\"cooldownReset('snikers');\"]").click()
            self.player.snickers -= 1
            random_delay()

    # FIGHTING SINGLE ENEMY
    def _search_enemy_by_level(
        self,
        enemy_level_min: Optional[int] = None,
        enemy_level_max: Optional[int] = None,
    ) -> None:
        """
        TBA
        """
        if not self.player.is_major:
            logger.error("Player is not a major, can't fight enemies by level.")
            return None

        # Show search bar if not displayed
        is_displ = self.driver.find_element(By.ID, "search-enemy-bar").get_attribute("style")
        if is_displ == "display: none;":
            logger.info("Search enemy bar is hidden. Clicking to display it.")
            self.driver.find_element(
                By.XPATH, "//span[@class='dashedlink' and @onclick='toggleSearchEnemyBar();']"
            ).click()
            random_delay()

        # Set enemy min level
        enemy_level_min = enemy_level_min or self.player.level + 1
        logger.info(f"Setting enemy minimum level to {enemy_level_min}.")
        enemy_level_min_str = str(enemy_level_min)

        set_enemy_level_min_el = self.driver.find_element(By.NAME, "minlevel")
        curr_value_min = set_enemy_level_min_el.get_attribute("value")
        if curr_value_min != enemy_level_min_str:
            logger.info(f"Enemy minimum level is not {enemy_level_min_str}. Updating it.")
            set_enemy_level_min_el.clear()
            set_enemy_level_min_el.send_keys(enemy_level_min_str)
            random_delay()

        # Set enemy max level
        enemy_level_max = enemy_level_max or self.player.level + 1
        logger.info(f"Setting enemy maximum level to {enemy_level_max}.")
        enemy_level_max_str = str(enemy_level_max)

        set_enemy_level_max_el = self.driver.find_element(By.NAME, "maxlevel")
        value_max = set_enemy_level_max_el.get_attribute("value")
        if value_max != enemy_level_max_str:
            logger.info(f"Enemy maximum level is not {enemy_level_max_str}. Updating it.")
            set_enemy_level_max_el.clear()
            set_enemy_level_max_el.send_keys(enemy_level_max_str)
            random_delay()

        self.driver.find_element(By.XPATH, '//div[contains(text(), "Искать противника")]').click()
        random_delay()

    def start_enemy_search(
        self,
        enemy_search_type: EnemySearchType,
        enemy_level_min: Optional[int] = None,
        enemy_level_max: Optional[int] = None,
    ) -> None:
        """
        TBA
        """
        logger.info(f"Starting enemy search of type: {enemy_search_type}")

        if self.if_rest_timer():
            logger.error("Player is resting, can't start search")
            return None

        if enemy_search_type == enemy_search_type.WEAK:
            self.driver.find_element(By.CSS_SELECTOR, ".button-big.btn.f1").click()
            random_delay()
        elif enemy_search_type == enemy_search_type.EQUAL:
            self.driver.find_element(By.CSS_SELECTOR, ".button-big.btn.f2").click()
            random_delay()
        elif enemy_search_type == enemy_search_type.STRONG:
            self.driver.find_element(By.CSS_SELECTOR, ".button-big.btn.f3").click()
            random_delay()
        elif enemy_search_type == enemy_search_type.BY_NAME:
            pass
        elif enemy_search_type == enemy_search_type.BY_LEVEL:
            self._search_enemy_by_level(enemy_level_min, enemy_level_max)

    def fight_random_enemy_by_level(
        self,
        enemy_level_min: Optional[int] = None,
        enemy_level_max: Optional[int] = None,
    ) -> None:
        """
        Finds and fights a random enemy in the alley.

        Behavior:
            1. Ensures the driver is on the alley page.
            2. Checks and resets the rest timer if necessary.
            3. Ensures the enemy search bar is displayed.
            4. Sets the minimum and maximum enemy levels to predefined values.
            5. Finds an enemy and initiates an attack.
            6. Returns the driver to the alley page after the fight.
        """
        logger.info("Starting fight with random enemy by level.")

        if self.driver.current_url != self.BASE_URL:
            self.open()

        # Check if player is a major
        if not self.player.is_major:
            logger.error("Player is not a major, can't fight enemies by level.")
            return None

        # Restore heath if not full
        self.player.update_health_and_energy(is_refresh=False, verbose=False)
        if self.player.currenthp_prc != 1.0:
            logger.info("Player health is not full. Restoring health.")
            self.player.restore_health()

        # Reset rest timer if needed
        timer_el = self.driver.find_element(By.CLASS_NAME, "timer")
        timer_value = timer_el.get_attribute("timer")
        if timer_value and "-" not in timer_value:
            logger.info("Player is on rest. Trying to eat sneakers to reset the timer.")

            try:
                restore_snikers_el = self.driver.find_element(
                    By.XPATH,
                    "//div[@onclick=\"cooldownReset('snikers');\"]",
                )
                restore_snikers_el.click()
                random_delay()

                self.player.snickers -= 1
            except NoSuchElementException:
                logger.error("Can't eat sneakers, player is still on rest.")
                return None

        # Show search bar if not displayed
        is_displ = self.driver.find_element(By.ID, "search-enemy-bar").get_attribute("style")
        if is_displ == "display: none;":
            logger.info("Search enemy bar is hidden. Clicking to display it.")
            display_all_el = self.driver.find_element(
                By.XPATH,
                "//span[@class='dashedlink' and @onclick='toggleSearchEnemyBar();']",
            )
            display_all_el.click()
            random_delay()

        # Set enemy min level
        if enemy_level_min is None:
            logger.info("Enemy minimum level is not specified. Setting it to player level + 1.")
            enemy_level_min = self.player.level + 1
        enemy_level_min_str = str(enemy_level_min)

        set_enemy_level_min_el = self.driver.find_element(By.NAME, "minlevel")
        curr_value_min = set_enemy_level_min_el.get_attribute("value")
        if curr_value_min != enemy_level_min_str:
            logger.info(f"Enemy minimum level is not {enemy_level_min_str}. Updating it.")
            set_enemy_level_min_el.clear()
            set_enemy_level_min_el.send_keys(enemy_level_min_str)
            random_delay()

        # Set enemy max level
        if enemy_level_max is None:
            logger.info("Enemy maximum level is not specified. Setting it to player level + 1.")
            enemy_level_max = self.player.level + 1
        enemy_level_max_str = str(enemy_level_max)

        set_enemy_level_max_el = self.driver.find_element(By.NAME, "maxlevel")
        value_max = set_enemy_level_max_el.get_attribute("value")
        if value_max != enemy_level_max_str:
            logger.info(f"Enemy maximum level is not {enemy_level_max_str}. Updating it.")
            set_enemy_level_max_el.clear()
            set_enemy_level_max_el.send_keys(enemy_level_max_str)
            random_delay()

        # Find enemy to attack
        logger.info("Finding an enemy to attack.")
        find_enemy_major_el = self.driver.find_element(
            By.XPATH, '//div[contains(text(), "Искать противника")]'
        )
        find_enemy_major_el.click()
        random_delay()

        finished_enemy_search = False
        while not finished_enemy_search:
            player_stats_sum = (
                self.player.health
                + self.player.strength
                + self.player.dexterity
                + self.player.resistance
                + self.player.intuition
                + self.player.attention
                + self.player.charism
            )

            enemy_stat_elements = self.driver.find_elements(
                By.XPATH,
                '//td[@class="fighter2-cell"]//ul[@class="stats"]//span[@class="num"]',
            )
            enemy_stat_values = [int(element.text) for element in enemy_stat_elements]
            enemy_stats_sum = sum(enemy_stat_values)

            if enemy_stats_sum > player_stats_sum:
                logger.warning("Enemy stats are too high, trying to find another enemy.")
                find_another_el = self.driver.find_element(
                    By.XPATH, '//a[contains(@href, "/alley/search/again/")]'
                )
                find_another_el.click()
                random_delay()
            else:
                logger.info("Enemy found, attacking.")
                finished_enemy_search = True

        # Attack enemy
        attack_enemy_el = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='button button-fight']"))
        )
        attack_enemy_el.click()
        random_delay()

        # Return to the alley
        self.driver.get(self.BASE_URL)
        random_delay()
        logger.info("Finished fight with random enemy.")

    def start_patrol(self, patrol_minutes: int) -> None:
        """
        Starts a patrol for a specified duration if no patrol is currently active.

        Parameters:
            patrol_minutes (int): The duration of the patrol in minutes.
                                Valid options are 20 or 40 minutes.

        TODO:
            1. Implement a countdown to track remaining patrol time.
            2. Introduce an enum to enforce valid patrol duration options.
            4. Verify if the patrol was successfully initiated or if the location was unavailable.
            5. Finish caravan check code
            6. add player parameter, when patrol will end, by which time patrol will end
            the logic should be the following:
                1. check patrol status from player class
                2. check if time is over and patrol is finished from player class
                3. try to find the button to start the patrol just to be sure
                4. start the patrol
                5. update player patrol status
                6. do the same for work and patriot tv
        """
        logger.info(f"Starting patrol for {patrol_minutes} minutes.")
        self.open()

        # Transform minutes to string
        patrol_minutes_str = str(patrol_minutes) + " минут"
        logger.info(f"Transforming minutes to string: {patrol_minutes_str}")

        # Check if there are no more minutes to patrol (later use player class to check how many minutes left)
        try:
            self.driver.find_element(
                By.XPATH,
                "//p[text()='На сегодня Вы уже истратили все время патрулирования.']",
            )
            logger.error("Can't start the patrol, there are no more minutes to patrol.")
            return None
        except NoSuchElementException:
            pass

        # Check if patrol is already started
        try:
            leave_patrol_button = self.driver.find_element(By.XPATH, '//*[@id="leave-patrol-button"]')
            self.player.on_patrol = True
            logger.error("Can't start the patrol, player is already in patrol.")
            return None
        except NoSuchElementException:
            pass

        # Start patrol
        select_patrol_minutes_el = Select(
            self.driver.find_element(By.XPATH, '//*[@id="patrolForm"]/div[2]/select')
        )
        select_patrol_minutes_el.select_by_visible_text(patrol_minutes_str)
        random_delay()

        start_patrol_el = self.driver.find_element(
            By.XPATH, '//button[@id="alley-patrol-button" and @class="button"]'
        )
        start_patrol_el.click()
        random_delay()

        # Handle caravan
        try:
            caravan_el_1 = self.driver.find_element(By.XPATH, "//*[@href='/desert/']")
            logger.info("Caravan appeared, handling caravan.")
            caravan_el_1.click()
            random_delay()

            caravan_el_2 = self.driver.find_element(By.XPATH, "//*[contains(@onclick, '/desert/rob/')]")
            caravan_el_2.click()
            random_delay()

            result_text = self.driver.find_element(By.CLASS_NAME, "text").text
            farmed_money = 0
            if result_text.startswith("К сожалению"):
                logger.info("Caravan farm failed :(")
            else:
                logger.info(f"Caravan farm successfully completed. Farmed {farmed_money}.")
            self.driver.get(self.BASE_URL)
            random_delay()
        except NoSuchElementException:
            pass

        # Update player status
        self.player.on_patrol = True
        self.player.patrol_time_left -= patrol_minutes
        logger.info("Patrol successfully started.")
        return None

    def watch_patriot_TV(self, watch_hours: int) -> None:
        """
        Starts a patriot TV session for a specified duration if not currently active.

        Parameters:
            watch_hours (int): The duration of the watching session in hours.
                                Valid option is 1 hour.

        TODO:
            1. update player parameter, when watching will end, by which time watching will end and how many hours left
        """
        logger.info(f"Starting patriot TV session for {watch_hours} hours.")
        self.open()

        # Transform minutes to string
        watch_hours_str = str(watch_hours) + " час"
        logger.info(f"Transforming hours to string: {watch_hours_str}")

        # Start watching sessing if not already started
        try:
            select_watch_hours_el = Select(
                self.driver.find_element(By.XPATH, '//*[@id="patriottvForm"]/div/select')
            )
        except NoSuchElementException:
            logger.error(
                "Can't start watching patriot TV, no hours left or player is watching patriot TV right now."
            )
            return None

        select_watch_hours_el.select_by_visible_text(watch_hours_str)
        random_delay()

        start_watch_el = self.driver.find_element(By.XPATH, '//*[@id="alley-patrol-button"]')
        start_watch_el.click()
        random_delay()

        # Update player status
        self.player.on_watch_patriot_TV = True
        self.player.watch_patriot_TV_time_left -= watch_hours
        logger.info("Patriot TV session successfully started.")
        return None

import re
from math import e
from typing import Literal, Optional

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


class Alley:
    """
    Represents the 'Alley' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the Alley page.
    """

    # TODO: optimize locators if possible
    BASE_URL = "https://www.moswar.ru/alley/"
    LOCATORS = {
        # Timers
        "rest_timer": (By.XPATH, "//span[@class='timer' and contains(@trigger, 'end_alley_cooldown')]"),
        "rest_reset_enegry": (By.XPATH, "//div[@onclick=\"cooldownReset('tonus');\"]"),
        "rest_reset_snikers": (By.XPATH, "//div[@onclick=\"cooldownReset('snikers');\"]"),
        # Enemy search
        "enemy_weak": (By.CSS_SELECTOR, ".button-big.btn.f1"),
        "enemy_equal": (By.CSS_SELECTOR, ".button-big.btn.f2"),
        "enemy_strong": (By.CSS_SELECTOR, ".button-big.btn.f3"),
        "enemy_major_bar": (By.ID, "search-enemy-bar"),
        "enemy_major_bar_toggle": (
            By.XPATH,
            "//span[@class='dashedlink' and @onclick='toggleSearchEnemyBar();']",
        ),
        "enemy_level_min": (By.NAME, "minlevel"),
        "enemy_level_max": (By.NAME, "maxlevel"),
        "enemy_level_find": (By.XPATH, '//div[contains(text(), "Искать противника")]'),
        "enemy_name_input": "TBA",
        "enemy_name_find": "TBA",
        # Patrol
        "patrol_start_button": (By.XPATH, '//button[@id="alley-patrol-button" and @class="button"]'),
        "patrol_leave_button": "TBA",
        "patrol_select_minutes": (By.XPATH, '//*[@id="patrolForm"]/div[2]/select'),
        "patrol_active": (By.XPATH, "//td[@class='label' and text()='Патрулирование:']"),
        "patrol_time_left": (By.XPATH, '//form[@class="patrol" and @id="patrolForm"]//p[@class="timeleft"]'),
        # Caravan
        "caravan_available": (By.XPATH, "//a[@href='/desert/']"),
        "caravan_rob": (By.XPATH, "//a[contains(@href, '/desert/rob/')]"),
        "caravan_result": (By.CLASS_NAME, "text"),
        # Patriot TV
        "TV_select_hours": (By.XPATH, '//*[@id="patriottvForm"]/div/select'),
        "TV_start_button": (By.XPATH, '//*[@id="alley-patriot-button"]'),
        "TV_active": (By.XPATH, "//td[@class='label' and text()='Просмотр:']"),
        "TV_time_left": (By.XPATH, '//form[@class="patrol" and @id="patriottvForm"]//p[@class="timeleft"]'),
    }

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

    # FIGHTING SINGLE ENEMY
    def is_rest_active(self) -> bool:
        """
        Checks if the player is currently resting.
        """
        timer_value = self.driver.find_element(*self.LOCATORS["rest_timer"]).get_attribute("timer")
        if timer_value and timer_value.count("-") > 0:
            self.player.on_rest = False
            return False
        else:
            self.player.on_rest = True
            return True

    def reset_timer(self, reset_timer_type: ResetTimerType) -> None:
        """
        Resets the rest timer by using energy or snickers.
        """
        if not self.is_rest_active():
            logger.error("Player is not resting, can't reset the timer.")
            return None

        if reset_timer_type == reset_timer_type.ENERGY:
            logger.info("Resetting energy timer by using enegry.")
            self.driver.find_element(*self.LOCATORS["rest_reset_enegry"]).click()
            random_delay()
        elif reset_timer_type == reset_timer_type.SNICKERS:
            logger.info("Resetting rest timer by using sneakers.")

            if self.player.snickers == 0:
                logger.error("Player has no sneakers to reset the timer.")
                return None

            self.driver.find_element(*self.LOCATORS["rest_reset_snikers"]).click()
            self.player.snickers -= 1
            random_delay()

        random_delay(min_time=5, max_time=6)
        self.driver.refresh()
        if not self.is_rest_active():
            logger.info("Rest timer successfully reset.")
        else:
            logger.error("Failed to reset rest timer, player is still resting.")

    def _search_enemy_by_level(
        self,
        enemy_level_min: Optional[int] = None,
        enemy_level_max: Optional[int] = None,
    ) -> None:
        """
        Start enemy search by level.

        Parameters:
            enemy_level_min (Optional[int]): Minimum level of the enemy to search for. Defaults to None.
            enemy_level_max (Optional[int]): Maximum level of the enemy to search for. Defaults to None.
        """
        if not self.player.is_major:
            logger.error("Player is not a major, can't fight enemies by level.")
            return None

        # Show search bar if not displayed
        is_displ = self.driver.find_element(*self.LOCATORS["enemy_major_bar"]).get_attribute("style")
        if is_displ == "display: none;":
            logger.info("Search enemy bar is hidden. Clicking to display it.")
            self.driver.find_element(*self.LOCATORS["enemy_major_bar_toggle"]).click()
            random_delay()

        # Set enemy min level
        enemy_level_min = enemy_level_min or self.player.level + 1
        logger.info(f"Setting enemy minimum level to {enemy_level_min}.")
        enemy_level_min_str = str(enemy_level_min)

        set_enemy_level_min_el = self.driver.find_element(*self.LOCATORS["enemy_level_min"])
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

        set_enemy_level_max_el = self.driver.find_element(*self.LOCATORS["enemy_level_max"])
        value_max = set_enemy_level_max_el.get_attribute("value")
        if value_max != enemy_level_max_str:
            logger.info(f"Enemy maximum level is not {enemy_level_max_str}. Updating it.")
            set_enemy_level_max_el.clear()
            set_enemy_level_max_el.send_keys(enemy_level_max_str)
            random_delay()

        self.driver.find_element(*self.LOCATORS["enemy_level_find"]).click()
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

        if self.is_rest_active():
            logger.error("Player is resting, can't start enemy search.")
            return None

        if enemy_search_type == enemy_search_type.WEAK:
            self.driver.find_element(*self.LOCATORS["enemy_weak"]).click()
            random_delay()
        elif enemy_search_type == enemy_search_type.EQUAL:
            self.driver.find_element(*self.LOCATORS["enemy_equal"]).click()
            random_delay()
        elif enemy_search_type == enemy_search_type.STRONG:
            self.driver.find_element(*self.LOCATORS["enemy_strong"]).click()
            random_delay()
        elif enemy_search_type == enemy_search_type.BY_NAME:
            pass
        elif enemy_search_type == enemy_search_type.BY_LEVEL:
            self._search_enemy_by_level(enemy_level_min, enemy_level_max)

        if not self.driver.current_url.startswith(self.BASE_URL + "search/"):
            logger.error("Failed to start enemy search, driver is not on the search page.")

    #     # Reset rest timer if needed
    #     timer_el = self.driver.find_element(By.CLASS_NAME, "timer")
    #     timer_value = timer_el.get_attribute("timer")
    #     if timer_value and "-" not in timer_value:
    #         logger.info("Player is on rest. Trying to eat sneakers to reset the timer.")

    #         try:
    #             restore_snikers_el = self.driver.find_element(
    #                 By.XPATH,
    #                 "//div[@onclick=\"cooldownReset('snikers');\"]",
    #             )
    #             restore_snikers_el.click()
    #             random_delay()

    #             self.player.snickers -= 1
    #         except NoSuchElementException:
    #             logger.error("Can't eat sneakers, player is still on rest.")
    #             return None

    #     # Show search bar if not displayed
    #     is_displ = self.driver.find_element(By.ID, "search-enemy-bar").get_attribute("style")
    #     if is_displ == "display: none;":
    #         logger.info("Search enemy bar is hidden. Clicking to display it.")
    #         display_all_el = self.driver.find_element(
    #             By.XPATH,
    #             "//span[@class='dashedlink' and @onclick='toggleSearchEnemyBar();']",
    #         )
    #         display_all_el.click()
    #         random_delay()

    #     # Set enemy min level
    #     if enemy_level_min is None:
    #         logger.info("Enemy minimum level is not specified. Setting it to player level + 1.")
    #         enemy_level_min = self.player.level + 1
    #     enemy_level_min_str = str(enemy_level_min)

    #     set_enemy_level_min_el = self.driver.find_element(By.NAME, "minlevel")
    #     curr_value_min = set_enemy_level_min_el.get_attribute("value")
    #     if curr_value_min != enemy_level_min_str:
    #         logger.info(f"Enemy minimum level is not {enemy_level_min_str}. Updating it.")
    #         set_enemy_level_min_el.clear()
    #         set_enemy_level_min_el.send_keys(enemy_level_min_str)
    #         random_delay()

    #     # Set enemy max level
    #     if enemy_level_max is None:
    #         logger.info("Enemy maximum level is not specified. Setting it to player level + 1.")
    #         enemy_level_max = self.player.level + 1
    #     enemy_level_max_str = str(enemy_level_max)

    #     set_enemy_level_max_el = self.driver.find_element(By.NAME, "maxlevel")
    #     value_max = set_enemy_level_max_el.get_attribute("value")
    #     if value_max != enemy_level_max_str:
    #         logger.info(f"Enemy maximum level is not {enemy_level_max_str}. Updating it.")
    #         set_enemy_level_max_el.clear()
    #         set_enemy_level_max_el.send_keys(enemy_level_max_str)
    #         random_delay()

    #     # Find enemy to attack
    #     logger.info("Finding an enemy to attack.")
    #     find_enemy_major_el = self.driver.find_element(
    #         By.XPATH, '//div[contains(text(), "Искать противника")]'
    #     )
    #     find_enemy_major_el.click()
    #     random_delay()

    #     finished_enemy_search = False
    #     while not finished_enemy_search:
    #         player_stats_sum = (
    #             self.player.health
    #             + self.player.strength
    #             + self.player.dexterity
    #             + self.player.resistance
    #             + self.player.intuition
    #             + self.player.attention
    #             + self.player.charism
    #         )

    #         enemy_stat_elements = self.driver.find_elements(
    #             By.XPATH,
    #             '//td[@class="fighter2-cell"]//ul[@class="stats"]//span[@class="num"]',
    #         )
    #         enemy_stat_values = [int(element.text) for element in enemy_stat_elements]
    #         enemy_stats_sum = sum(enemy_stat_values)

    #         if enemy_stats_sum > player_stats_sum:
    #             logger.warning("Enemy stats are too high, trying to find another enemy.")
    #             find_another_el = self.driver.find_element(
    #                 By.XPATH, '//a[contains(@href, "/alley/search/again/")]'
    #             )
    #             find_another_el.click()
    #             random_delay()
    #         else:
    #             logger.info("Enemy found, attacking.")
    #             finished_enemy_search = True

    #     # Attack enemy
    #     attack_enemy_el = WebDriverWait(self.driver, 10).until(
    #         EC.presence_of_element_located((By.XPATH, "//div[@class='button button-fight']"))
    #     )
    #     attack_enemy_el.click()
    #     random_delay()

    #     # Return to the alley
    #     self.driver.get(self.BASE_URL)
    #     random_delay()
    #     logger.info("Finished fight with random enemy.")

    # PATROL
    def is_patrol_active(self) -> bool:
        """
        Checks if the player is currently on patrol.
        """
        try:
            self.driver.find_element(*self.LOCATORS["patrol_active"])
            self.player.on_patrol = True
            return True
        except NoSuchElementException:
            self.player.on_patrol = False
            return False

    # TODO: check if correct when no time left
    def get_patrol_time_left(self) -> int:
        """
        Returns the remaining patrol time in minutes.
        """
        try:
            time_left_el = self.driver.find_element(*self.LOCATORS["patrol_time_left"])
            time_left = int(time_left_el.text.split(" ")[-2])
        except Exception:
            time_left = 0

        self.player.patrol_time_left = time_left
        return time_left

    def start_patrol(self, patrol_minutes: Literal[20, 40] = 20) -> None:
        """
        TBA
        """
        logger.info(f"Starting patrol for {patrol_minutes} minutes.")

        if patrol_minutes not in [20, 40]:
            logger.error("Invalid patrol minutes. Valid options are 20 or 40 minutes.")
            return None

        if self.is_patrol_active():
            logger.error("Can't start patrol, player is already on patrol.")
            return None

        patrol_time_left = self.get_patrol_time_left()
        if patrol_time_left < patrol_minutes:
            logger.error(
                f"Can't start patrol for {patrol_minutes} minutes, only {self.player.patrol_time_left} minutes left."
            )
            return None

        patrol_minutes_str = str(patrol_minutes) + " минут"
        select_patrol_minutes_el = Select(self.driver.find_element(*self.LOCATORS["patrol_select_minutes"]))
        select_patrol_minutes_el.select_by_visible_text(patrol_minutes_str)
        random_delay()

        start_patrol_el = self.driver.find_element(*self.LOCATORS["patrol_start_button"])
        start_patrol_el.click()
        random_delay(min_time=5, max_time=6)

        if self.is_patrol_active():
            self.player.patrol_time_left -= patrol_minutes
            logger.info(
                f"Patrol successfully started, patrol time left: {self.player.patrol_time_left} minutes."
            )
        else:
            logger.error("Failed to start patrol")

    # CARAVAN
    # TODO: test caravan functions
    def is_caravan_available(self) -> bool:
        """
        Checks if a caravan is available in the alley.
        """
        try:
            self.driver.find_element(*self.LOCATORS["caravan_available"])
            return True
        except NoSuchElementException:
            return False

    def rob_caravan(self) -> None:
        """
        Attempts to rob the caravan if available.
        """
        if not self.is_caravan_available():
            logger.error("No caravan available to rob.")
            return None

        try:
            caravan_el_1 = self.driver.find_element(*self.LOCATORS["caravan_available"])
            caravan_el_1.click()
            random_delay()

            caravan_el_2 = self.driver.find_element(*self.LOCATORS["caravan_rob"])
            caravan_el_2.click()
            random_delay()

            result_text = self.driver.find_element(*self.LOCATORS["caravan_result"]).text
            if result_text.startswith("К сожалению"):
                logger.info("Caravan farm failed :(")
            else:
                logger.info(f"Caravan farm successfully completed. Result: {result_text}")
                self.player.money += 0  # TODO: Update with actual money farmed
        except NoSuchElementException:
            logger.error("Error while trying to rob the caravan")

        self.open()

    # PATRIOT TV
    def is_TV_active(self) -> bool:
        """
        Checks if the player is currently watching Patriot TV.
        """
        try:
            self.driver.find_element(*self.LOCATORS["TV_active"])
            self.player.on_TV = True
            return True
        except NoSuchElementException:
            self.player.on_TV = False
            return False

    # TODO: check if correct
    def get_TV_time_left(self) -> int:
        """
        Returns the remaining Patriot TV watching time in minutes.
        """
        try:
            time_left_el = self.driver.find_element(*self.LOCATORS["TV_time_left"])
            time_left = int(time_left_el.text.split(" ")[-2])
        except Exception:
            time_left = 0

        self.player.TV_time_left = time_left
        return time_left

    # TODO: check if correct
    def start_watching_TV(self, watch_hours: Literal[1] = 1) -> None:
        """
        TBA
        """
        logger.info(f"Starting Patriot TV session for {watch_hours} hour(s).")

        if watch_hours != 1:
            logger.error("Invalid watch hours. Only 1 hour is allowed.")
            return None

        if self.is_TV_active():
            logger.error("Can't start watching Patriot TV, player is already watching.")
            return None

        watch_time_left = self.get_TV_time_left()
        if watch_time_left < watch_hours:
            logger.error(
                f"Can't start watching Patriot TV for {watch_hours} hour(s), only {self.player.TV_time_left} hours left."
            )
            return None

        select_watch_hours_el = Select(self.driver.find_element(*self.LOCATORS["TV_select_hours"]))
        select_watch_hours_el.select_by_visible_text(f"{watch_hours} час")
        random_delay()

        start_watch_el = self.driver.find_element(*self.LOCATORS["TV_start_button"])
        start_watch_el.click()
        random_delay(min_time=5, max_time=6)

        if self.is_TV_active():
            self.player.TV_time_left -= watch_hours
            logger.info(
                f"Patriot TV session successfully started, time left: {self.player.TV_time_left} hours."
            )
        else:
            logger.error("Failed to start Patriot TV session")

from typing import Literal

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

from entities.player import Player
from utils.custom_logging import logger
from utils.human_simulation import random_delay

# TODO:
# 2. use Enum for items in use_item function
# 3. add return of time left before the next training available?
# 4. change approach to use item, try to find item address by picture name
# 5. add new items (ошейник)


class PetForFightMain:
    """
    A class to manage a pet in the game for training, updating stats, and using items.

    Attributes:
        pet_ids (dict): A dictionary mapping pet names to their unique IDs.
        item_ids (dict): A dictionary mapping item names to their unique IDs.
        player: The player object controlling the pet.
        driver: The Selenium WebDriver instance.
        name (str): The name of the pet.
        pet_id (int): The unique ID of the pet.
        BASE_URL (str): The base URL for the pet's arena page.
        currenthp (int): The current health of the pet.
        currenthp_max (int): The maximum health of the pet.
        currenthp_prc (float): The current health percentage of the pet.
        focus (int): The focus stat of the pet.
        loyality (int): The loyalty stat of the pet.
        mass (int): The mass stat of the pet.
    """

    pet_ids = {
        "Абиссинский Бог": 2471779,
        "Пантера": 2431326,
        "Доберман": 1998999,
        "Чихуа-хуа": 2428452,
        "Котенок по имени 'ГАФ'": 2468340,
    }

    item_img_links = {"Косточка": "/@/images/obj/gifts/gift-1.png"}

    def __init__(self, player: Player, driver: WebDriver, name: str):
        """
        Initializes the PetForFightMain instance.

        Parameters:
            player (Player): The player object controlling the pet.
            driver (WebDriver): Selenium WebDriver instance for interacting with the game's web interface.
            name (str): The name of the pet.

        Raises:
            ValueError: If the provided pet name is not in the pet_ids dictionary.
        """
        if name not in self.pet_ids:
            raise ValueError(
                f"Invalid pet name: {name}. Supported names are: {list(self.pet_ids.keys())}"
            )
        self.player = player
        self.driver = driver
        self.name = name
        self.pet_id = self.pet_ids[name]
        self.BASE_URL = f"https://www.moswar.ru/petarena/train/{self.pet_id}/"

        # Pet health
        self.currenthp = 0.0
        self.currenthp_max = 0.0
        self.currenthp_prc = 0.0

        # Pet stats
        self.focus = 0
        self.loyality = 0
        self.mass = 0

        self.update_pet_info()
        logger.info(f"Pet '{self.name}' successfully initialized.")

    def open(self) -> None:
        """
        This method ensures the driver is on the pet page by navigating to its URL.
        """
        if self.driver.current_url != self.BASE_URL:
            logger.info(
                f"Driver is not on the '{self.name}' pet page, navigating to it."
            )
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info(f"Driver is already on the '{self.name}' pet page, refreshing.")
            self.driver.refresh()
            random_delay()

    # TODO: update using setattr function
    def update_pet_info(self) -> None:
        """
        Updates the information about pet's stats and health by retrieving the information from the webpage.
        """
        logger.info(f"Updating '{self.name}' pet stats and heatlh info.")
        self.open()

        # Health
        hp_el = self.driver.find_element(By.XPATH, '//span[@id="pethp"]')
        self.currenthp = float(hp_el.text.split("/")[0])
        self.currenthp_max = float(hp_el.text.split("/")[1])
        self.currenthp_prc = self.currenthp / self.currenthp_max

        # Focus
        focus_el = self.driver.find_element(
            By.XPATH, '//li[@rel="focus"]//span[@class="num"]'
        )
        self.focus = int(focus_el.text)

        # Loyality
        loyality_el = self.driver.find_element(
            By.XPATH, '//li[@rel="loyality"]//span[@class="num"]'
        )
        self.loyality = int(loyality_el.text)

        # Mass
        mass_el = self.driver.find_element(
            By.XPATH, '//li[@rel="mass"]//span[@class="num"]'
        )
        self.mass = int(mass_el.text)

    def train(self, skill_to_train: Literal["focus", "loyality", "mass"]) -> None:
        """
        Trains the specified skill for the pet.

        This function attempts to train the pet's specified skill, checking if the pet is
        available for training and ensuring the skill is valid. If the pet is resting or
        the skill is unavailable, appropriate error messages will be logged.

        Parameters:
            skill_to_train (Literal["focus", "loyality", "mass"]): The skill to train.
            It can be one of the following:
                - "focus": Focus skill
                - "loyality": Loyality skill
                - "mass": Mass skill
        """
        logger.info(f"Training '{skill_to_train}' for '{self.name}' pet.")
        self.open()

        # Check if pet is on rest
        try:
            self.driver.find_element(
                By.XPATH, '//*[contains(text(), "Питомец отдыхает")]'
            )
            logger.error("Pet is on rest, can't train.")
            return None
        except NoSuchElementException:
            pass

        # Find skill address and train
        try:
            train_el = self.driver.find_element(
                By.XPATH, f'//button[contains(@onclick, "{skill_to_train}")]'
            )
        except NoSuchElementException:
            logger.error(f"Skill '{skill_to_train}' is not available for training.")
            return None

        train_el.click()
        random_delay()
        logger.info(f"Started training '{skill_to_train}' for '{self.name}' pet.")
        return None

    def use_item(self, item: str, times: int) -> None:
        """
        Uses the specified item on the pet a given number of times.

        This function tries to find the specified item on the page and uses it on the pet the
        specified number of times. If there aren't enough items available or the item isn't
        supported or found, error messages are logged. The item is used by clicking on it in
        the browser, with random delays between each use.

        Parameters:
            item (str): The name of the item to use.
            times (int): The number of times to use the item.
        """
        logger.info(f"Using {item} for {times} times.")
        self.open()

        # Create element objects for item
        if item not in self.item_img_links.keys():
            logger.error(f"Item '{item}' is not supported.")
            return None

        item_img_link = self.item_img_links[item]
        item_el_addr = f'//img[@src="{item_img_link}"]/parent::div'

        try:
            item_el = self.driver.find_element(By.XPATH, item_el_addr)
        except NoSuchElementException:
            logger.error(f"Item '{item}' is not available.")
            return None

        count_el = item_el.find_element(By.XPATH, ".//div[@class='count']")
        action_el = item_el.find_element(By.XPATH, ".//div[@class='action']")

        # Stop function if there are less items available than we want to use
        count = int(count_el.text.replace("#", ""))
        if count < times:
            logger.error(
                f"Not enough '{item}' to use {times} times. There are only {count} available."
            )
            return None

        # Use items
        used_times = 0
        for _ in tqdm(range(times), desc=f"Using '{item}'"):
            try:
                action_el.click()
                used_times += 1
                random_delay(0.5, 1.5)
            except Exception as e:
                logger.error("Something went wrong while using the item, stopping.")
                logger.error(e)
                return None

        logger.info(f"Used '{item}' for {used_times} times.")
        return None

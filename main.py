from dotenv import load_dotenv
import os
import time
import re
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from configuration.configuration import set_options
from authorization import log_in
from locations.metro import Metro
from locations.alley import Alley
from locations.home import Home
from locations.locations_secondary import (
    Shaurburgers,
    Casino,
    Police,
    NightClub,
    Factory,
    TrainerVip,
)
from entities.player import Player
from entities.pets import PetForFightMain
from general_functions import go_on_activities
from tqdm import tqdm
from tqdm import trange

load_dotenv()

options = set_options()
driver = webdriver.Chrome(options=options)

# Login
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")
credentials = {"login": login, "password": password}
driver = log_in(driver, credentials)

# Player (fix cookies expiration)
player = Player(driver, update_info_on_init=True)
player.use_item("Полезный пельмень", 140)
player.show_info(show_all=True)

# Alley fighting
alley = Alley(player, driver)
for i in tqdm(range(2), desc="Fighting enemies"):
    alley.fight_random_enemy_by_level(16, 16)

# Casino test
casino = Casino(player, driver)
casino.buy_chips(20)

# Police test
police = Police(player, driver)
# police.open()

# NightClub test
nightclub = NightClub(player, driver)
nightclub.check_tatoo_timer()
# nightclub.open()

# Factory test
factory = Factory(player, driver)
factory.check_current_details_name()
# factory.buy_current_details()

# Home test
home = Home(player, driver)
home.check_mars_trip_timer()
# home.open("zodiac")

# TrainerVip test
trainer_vip = TrainerVip(player, driver)
trainer_vip.check_bojara_timer()
# trainer_vip.drink_Bojara()

# Routine to update statuses and start activities
alley = Alley(player, driver)
shaurburgers = Shaurburgers(player, driver)
# shaurburgers.start_work_shift(2)

# patror status update is not working
# work status update need to be fixed, do not 0 it if cannot update
while True:
    go_on_activities(player, alley, shaurburgers)

    if all(
        time_left == 0
        for time_left in [
            player.work_time_left,
            player.patrol_time_left,
            player.watch_patriot_TV_time_left,
        ]
    ):
        print("Stopping routine.")
        break

    # Generate a random sleep duration in seconds
    seconds_to_sleep = random.randint(41 * 60, 42 * 60)
    print(
        f"Sleeping for {seconds_to_sleep // 60} minutes and {seconds_to_sleep % 60} seconds."
    )

    # Use trange to show progress bar during sleep
    for _ in trange(
        seconds_to_sleep, desc="Sleeping", unit="s", colour="cyan", leave=False
    ):
        time.sleep(1)


# Metro
metro = Metro(player, driver)
metro.fight_rat()

# Pet "Абиссинский Бог" and "Котенок по имени 'ГАФ'"
pet_abyss = PetForFightMain(player, driver, "Абиссинский Бог")
pet_abyss.use_item("Косточка", 50)
pet_abyss.train("focus")

pet_gaf = PetForFightMain(player, driver, "Котенок по имени 'ГАФ'")
pet_gaf.train("loyality")


# maybe decorator to add try except?
# Save session status at the end of each session?
# mimic more human interactions, description in mimic_human_interactions.md
# add stop if page change is not working
# add timestemp when patrol and work will be finished
# add times when mars/tatoo/bojara will be available
# add refresh only last refresh was more than a 30 seconds ago
# ask Chat GPT to check all scripts, what can be improved?
# ask chat to check if documentation is up to date
# player use item should use dict of active items, also change counter if used
# create bluprint for the locations class and then create child classes for each location
# add decorator to open function which will check the last time driver performed any action on the page, is it possible?
# check ожидание боя чтобы не пытаться идти в битву когда занят

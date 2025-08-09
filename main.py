import os
import random
import re
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from tqdm import tqdm, trange

from authorization import log_in
from configuration.configuration import set_options
from entities.pets import PetForFightMain
from entities.player import Player
from general_functions import go_on_activities
from locations.alley import Alley
from locations.home import Home
from locations.locations_secondary import (
    Casino,
    Factory,
    NightClub,
    Police,
    Shaurburgers,
    TrainerVip,
)
from locations.metro import Metro
from schemas.alley import EnemySearchType, ResetTimerType

load_dotenv()

options = set_options()
driver = webdriver.Chrome(options=options)

# Login
login = os.getenv("LOGIN", "default_login")
password = os.getenv("PASSWORD", "default_password")
credentials = {"login": login, "password": password}
driver = log_in(driver, credentials)

# Player (TODO: fix cookies expiration)
player = Player(driver, update_info_on_init=True)
# player.use_item("Полезный пельмень", 140)
player.show_info(show_all=True)


# Alley fighting
alley = Alley(player, driver)

alley.open()

alley.is_patrol_active()
alley.get_patrol_time_left()
alley.start_patrol(40)

alley.is_TV_active()
alley.get_TV_time_left()
alley.start_watching_TV(1)


alley.is_rest_active()
alley.reset_rest_timer(ResetTimerType.ENERGY)
alley.start_enemy_search(EnemySearchType.BY_LEVEL, enemy_level_min=16, enemy_level_max=16)


timer = driver.find_element(By.XPATH, "//span[@class='timer' and contains(@trigger, 'end_alley_cooldown')]")


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

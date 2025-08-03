from entities.player import Player
from locations.alley import Alley
from locations.locations_secondary import Shaurburgers


# Routine to update statuses and start activities
# TODO: add docstrings
def go_on_activities(player: Player, alley: Alley, shaurburgers: Shaurburgers) -> None:
    player.update_battle_status(is_refresh=True, verbose=False)
    player.update_underground_status(is_refresh=False, verbose=False)

    if player.in_battle == False and player.in_underground == False:
        player.update_patrol_status()
        player.update_watch_patriot_TV_status()
        player.update_work_status()

        if player.on_patrol == False and player.patrol_time_left >= 40:
            alley.start_patrol(40)
            assert player.on_patrol == True
        if (
            player.on_watch_patriot_TV == False
            and player.watch_patriot_TV_time_left >= 1
        ):
            alley.watch_patriot_TV(1)
            assert player.on_watch_patriot_TV == True
        if player.on_work == False and player.work_time_left >= 2:
            shaurburgers.start_work_shift(2)
            assert player.on_work == True

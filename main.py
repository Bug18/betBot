from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
import time
import pandas as pd


def read_excel_file(path_to_file: str):
	return pd.read_excel(path_to_file, index_col=0)


def write_to_file(path_to_file: str, dataframe: pd.DataFrame):
	dataframe.to_excel(path_to_file)


def get_games():
	path = "/games.xlsx"

	driver = Firefox()
	driver.minimize_window()
	driver.get("https://sports.bwin.de/en/sports/basketball-7")

	time.sleep(5)

	class_team_names = "participants-pair-game"

	games = driver.find_elements(By.CLASS_NAME, class_team_names)
	games = [team.text.split("\n") for team in games]
	for game in games:
		if "@" in game:
			game.remove("@")

	games_frame = pd.DataFrame(data=games, columns=["Team1", "Team2"])
	write_to_file(path, games_frame)

	driver.quit()


def main():
	title = r"""
	__________        __    __  .__                 __________        __   
	\______   \ _____/  |__/  |_|__| ____    ____   \______   \ _____/  |_ 
	|    |  _// __ \   __\   __\  |/    \  / ___\   |    |  _//  _ \   __\
	|    |   \  ___/|  |  |  | |  |   |  \/ /_/  >  |    |   (  <_> )  |  
	|______  /\___  >__|  |__| |__|___|  /\___  /   |______  /\____/|__|  
	   	   \/     \/                   \//_____/           \/             
	""" + "\n" + "source: 'github.com/Bug18/betBot' all rights reserved."

	print(title)

	status = False

	get_games()

	command = input("Enter 'start' after modifying, saving and closing excel file > ")

	while not status:
		if command != "start":
			command = input("Enter 'start' after modifying excel file > ")
		else:
			status = True

	while status:
		pass

	path = "/games.xlsx"
	games = read_excel_file(path)
	print(games)


if __name__ == '__main__':
	main()

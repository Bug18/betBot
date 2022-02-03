from selenium.webdriver import Firefox, FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import time
import pandas as pd
from openpyxl import load_workbook
import json
import random


def get_login():
	with open("login.json", "r") as file:
		try:
			lines = json.load(file)
		except:
			return "-1", "-1"
		return lines["username"], lines["password"]



def write_login(u, p):
	with open("login.json", "w") as file:
		data = {
			"username": u,
			"password": p
		}
		file.write(json.dumps(data))


def read_excel_file(path_to_file: str):
	return pd.read_excel(path_to_file, sheet_name="bet games", index_col=0)


def write_to_file(path_to_file: str, dataframe: pd.DataFrame):
	book = load_workbook(path_to_file)
	writer = pd.ExcelWriter(path_to_file, engine='openpyxl')
	writer.book = book
	writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
	dataframe.to_excel(writer, "all games")
	writer.save()


def get_games(path):

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


def return_handicap_element_index(i):
	if i == 1:
		return 0
	elif i == 2:
		return 3


def wait_function():
	rand_int = random.randint(120, 240)

	for i in range(rand_int):
		print(f"Sleeping for: {rand_int - i} seconds{i // 5 * '.'}", end="\r")
		time.sleep(1)
	print("\n")



def bet(games: pd.DataFrame, username: str, password: str, timeout: float):

	timeout = timeout * 3600

	# web driver init start
	options = FirefoxOptions()
	options.set_preference("dom.popup_maximum", 0)
	driver = Firefox(options=options)
	actions = ActionChains(driver)
	driver.maximize_window()
	driver.wait = WebDriverWait(driver, 30)

	driver.get("https://sports.bwin.de/en/sports/live/basketball-7")

	print("Please manually close popup if it appears on screen. You have 20 seconds to close it!")
	# time.sleep(20)

	# accept all cookies
	try:
		driver.wait.until(ec.visibility_of_element_located((By.ID, "onetrust-accept-btn-handler"))).click()
	except:
		pass

	logged_in = False
	all_bets_placed = False

	start_time = time.time()

	while not all_bets_placed:
		print("Starting new cycle...\n")

		# check if login duration popup is up
		try:
			login_popup = driver.find_element(By.CLASS_NAME, "login-duration-content-inner")
			if login_popup:
				btns = driver.find_elements(By.CLASS_NAME, "btn")
				for btn in btns:
					if btn.text == "Continue":
						btn.click()
			time.sleep(2)
		except:
			pass

		# sort games by time
		try:
			sort_toggle_xpath = "/html/body/vn-app/vn-dynamic-layout-single-slot[4]/vn-main/main/div/ms-main/ng-scrollbar[1]/div/div/div/div/ms-main-column/div/ms-live/ms-live-event-list/div/ms-grid/ms-grid-header/div/ms-sort-selector/div[2]/div[2]/div[2]"
			driver.find_element(By.XPATH, sort_toggle_xpath).click()
			time.sleep(1)
		except:
			pass

		# get all currently available games
		class_participants = "participants-pair-game"
		class_game = "grid-event"
		class_live = "live-icon"
		all_games = driver.find_elements(By.CLASS_NAME, class_game)
		games_length = len(all_games)

		# go through all live games and bet if set
		for i in range(games_length):

			# get all currently available games
			class_game = "grid-event"
			all_games = driver.find_elements(By.CLASS_NAME, class_game)

			if len(all_games) < games_length:
				break

			current_game = all_games[i].find_element(By.CLASS_NAME, class_participants).text.split("\n")
			try:
				current_game.remove("@")
			except:
				pass

			print(f"Trying game: {current_game[0]} vs {current_game[1]}...")

			live = None
			try:
				live = all_games[i].find_element(By.CLASS_NAME, class_live)
			except:
				pass

			if live is None:
				print("Not live game! Continuing...")
				continue

			# check if game is on list to bet on
			team_to_bet_on_index = 0
			current_index_in_book = -1

			for j in range(len(games.index)):
				if games["Team1"][j] in current_game[0] and games["Team2"][j] in current_game[1] and int(games["Bet team"][j]) != -1:
					print(f"Opening game: {games['Team1'][j]} vs {games['Team2'][j]}...")
					team_to_bet_on_index = int(games["Bet team"][j])
					current_index_in_book = j

					# scroll into view
					desired_y = (all_games[i].size['height'] / 2) + all_games[i].location['y']
					current_y = (driver.execute_script('return window.innerHeight') / 2) + driver.execute_script(
						'return window.pageYOffset')
					scroll_y_by = desired_y - current_y
					driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
					time.sleep(1)

					all_games[i].click()
					break
				else:
					continue

			# go to next game if this one is not on the list to bet on
			else:
				print("Next game... This one is not on a list to bet on")
				continue

			# get spread values
			class_handicap = "name"
			class_score = "score-counter"
			class_bet_size = "stake-input-value"
			class_login_button = "betslip-place-button"
			email_field_name = "username"
			password_field_name = "password"
			login_button_xpath = "/html/body/div[6]/div[2]/div/mat-dialog-container/lh-login-dialog/lh-login/div/div/form/fieldset/section/div/button"

			score, handicaps = None, None

			try:
				driver.wait.until(ec.visibility_of_element_located((By.CLASS_NAME, class_handicap)))
				handicaps = driver.find_elements(By.CLASS_NAME, class_handicap)
				score = int(driver.find_elements(By.CLASS_NAME, class_score)[team_to_bet_on_index - 1].text.replace("\n", " ").split(" ")[0])
				state = True
			except:
				print("Data not available... Exiting this game...")
				state = False

			if state:
				if len(handicaps) > 0:
					try:
						handicap = float(handicaps[return_handicap_element_index(team_to_bet_on_index)].text.replace(",", "."))
						target_handicap = float(str(games["Spread"][current_index_in_book]).replace(",", "."))
						if handicap >= target_handicap:
							if score <= int(games["Max score"][current_index_in_book]):
								# select bet
								handicaps[return_handicap_element_index(team_to_bet_on_index)].click()

								# enter bet amount
								driver.wait.until(ec.visibility_of_element_located((By.CLASS_NAME, class_bet_size))).send_keys(float(games["Bet size"][current_index_in_book]))

								time.sleep(3)

								# find login button
								login_button = driver.find_element(By.CLASS_NAME, class_login_button)

								# scroll it into view
								desired_y = (login_button.size['height'] / 2) + login_button.location['y']
								current_y = (driver.execute_script('return window.innerHeight') / 2) + driver.execute_script(
									'return window.pageYOffset')
								scroll_y_by = desired_y - current_y
								driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
								time.sleep(2)

								# click login button
								login_button.click()

								time.sleep(5)

								if not logged_in:
									try:
										# enter login info
										driver.wait.until(
											ec.visibility_of_element_located((By.NAME, email_field_name))).send_keys(username)
										time.sleep(1)
										driver.find_element(By.NAME, password_field_name).send_keys(password)
										time.sleep(2)

										# click to login
										driver.find_element(By.XPATH, login_button_xpath).click()

										# time.sleep(10)

										driver.wait.until(ec.visibility_of_element_located((By.CLASS_NAME, "btn"))).click()

										logged_in = True
									except:
										pass

								# confirm bet if bet was selected
								try:
									class_bet_button_confirm = "betslip-place-button"
									driver.wait.until(ec.visibility_of_element_located((By.CLASS_NAME, class_bet_button_confirm))).click()
									print("Bet placed")
								except:
									pass

								# make sure bot doesn't bet again on the same team
								games.at[current_index_in_book, "Bet team"] = -1

								time.sleep(2)
							else:
								print("Game result too high...")
						else:
							print("Split to small...")
					except:
						print("Betting failed! Betting has probably stopped for this game.")
				else:
					print("Betting locked for this game!")

			# go back to main site
			print("Back to main site...")
			driver.get("https://sports.bwin.de/en/sports/live/basketball-7")
			time.sleep(5)

		# check if all wanted bets had been placed
		all_bets_placed = True

		for game in games["Bet team"]:
			if int(game) != -1:
				all_bets_placed = False

		if all_bets_placed:
			bets = driver.find_elements(By.CLASS_NAME, "sport-pick")
			if len(bets) == len(games["Bet team"]):
				print("All wanted bets placed! Exiting...")
				break
			else:
				print("Failed to place valid bets!")
				all_bets_placed = False

		if time.time() > start_time + timeout:
			print("Reached timeout, exiting...")
			all_bets_placed = True
			break

		print("Waiting to next cycle...\n")

		# waits before next cycle
		# time.sleep(random.randint(120, 240))
		wait_function()

	# close browser and exit script
	driver.quit()


def main():
	title = r"""
	__________        __    __  .__                 __________        __   
	\______   \ _____/  |__/  |_|__| ____    ____   \______   \ _____/  |_ 
	 |    |  _// __ \   __\   __\  |/    \  / ___\   |    |  _//  _ \   __\
	 |    |   \  ___/|  |  |  | |  |   |  \/ /_/  >  |    |   (  <_> )  |  
	 |______  /\___  >__|  |__| |__|___|  /\___  /   |______  /\____/|__|  
	 	\/     \/                   \//_____/           \/             
	""" + "\n" + "source: 'github.com/Bug18/betBot'"

	print(title)

	status = False
	path = ".\\games.xlsx"

	refresh_list = input("Refresh list of all available games? (y/n) >> ")
	if refresh_list == "y":
		print("Fetching and saving all available games... Please wait...\n")
		get_games(path)
		print("Games fetched and saved into games.xlsx in 'all games' sheet\n")

	command = input("Enter 'start' after modifying, saving and closing 'bet games' sheet >> ")

	while not status:
		if command != "start":
			command = input("Enter 'start' after modifying, saving and closing 'bet games' sheet >> ")
		else:
			status = True

	u, p = get_login()
	if u == "-1" and p == "-1":
		u = input("Enter app user id or email >> ")
		p = input("Enter app password >> ")
		write_login(u, p)

	games = read_excel_file(path)

	timeout = float(input("Enter timeout in hours >> "))
	print("Bot starting...\n")

	bet(games, u, p, timeout)

	exit(0)


if __name__ == '__main__':
	main()

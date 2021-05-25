import time
import json

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *


class BenchmarkBot:
    def __init__(self):
        self.running = True
        # Dict containing game name and game link in order to play them
        self.games = {}

        self.browser = webdriver.Chrome(executable_path=r"chromedriver.exe")

    def main(self):
        """Run the bot"""
        self.get_games()
        self.login()
        # Play all games
        for game in self.games:
            self.running = True
            self.browser.get(self.games[game])
            eval(f"self.{game.replace('-', '_')}")()
        # Show our scores
        self.browser.get("https://humanbenchmark.com/dashboard")
        # So the browser won't quit
        input()

    def reactiontime(self):
        """Plays the reaction time test (https://humanbenchmark.com/tests/reactiontime)"""
        # Get the element which should be pressed when the light turns green (also the start element)
        press_element = self.wait_for_element('//*[@id="root"]/div/div[4]/div[1]', True)

        # Start the game
        press_element.click()

        while self.running:
            element_class = press_element.get_attribute("class")
            # Screen is to be clicked
            if "waiting" not in element_class:
                press_element.click()
            # Game ended
            if "view-score" in element_class:
                self.running = False

        self.save('//*[@id="root"]/div/div[4]/div[1]/div/div/div[3]/button[1]')

    def sequence(self):
        """Plays the sequence memory test (https://humanbenchmark.com/tests/sequence)"""
        # Start the game
        start_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[2]/button', True
        )

        start_element.click()

        # Wait for the squares to load
        squares_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[2]/div', False
        )

        # The game consists of 3 rows of squares
        rows = squares_element.find_elements_by_xpath(".//*")

        # Get list of all squares in each row
        squares = [row.find_elements_by_xpath(f".//*") for row in rows]
        squares = [row for row in squares if row]

        # All active squares (i.e. the sequence)
        active_squares = []
        last_square = None
        level = 1

        while self.running:
            # Go over all squares and check which is active (should be clicked on)
            last_square, active_square = self.get_active_sequence_square(
                squares, last_square
            )

            if active_square:
                active_squares.append(active_square)

            # Wait until square get unactivated
            time.sleep(0.4)

            # Each x level x squares appear. So if there were x squares active, that means the level is over and
            # the bot should make his guesses
            if len(active_squares) >= level:
                time.sleep(0.1)

                # Suicide the bot
                if level == 30:
                    self.running = False
                    for i in range(31):
                        try:
                            squares[0][0].click()
                        except StaleElementReferenceException:
                            break
                    break

                # Click the active squares in the appropriate order
                for row_index, square_index in active_squares:
                    squares[row_index][square_index].click()
                active_squares = []
                level += 1

        self.save('//*[@id="root"]/div/div[4]/div[1]/div/div/div[3]/button[1]')

    @staticmethod
    def get_active_sequence_square(squares, last_square):
        for row_index, row in enumerate(squares):
            for square_index, square in enumerate(row):
                if square == last_square:
                    continue
                square_class = square.get_attribute("class")
                if "active" in square_class:
                    return square, (row_index, square_index)
        return None, ()

    def aim(self):
        """Plays the aim test (https://humanbenchmark.com/tests/aim)"""
        # Start the test
        start_element = self.wait_for_element('//*[@id="root"]/div/div[4]/div[1]', True)
        start_element.click()

        # Get the target to be clicked
        target_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div[1]/div/div/div/div[6]', True, 3
        )

        while self.running:
            try:
                # Click the target
                target_element.click()
                # Reload it
                target_element = self.wait_for_element(
                    '//*[@id="root"]/div/div[4]/div[1]/div/div[1]/div/div/div/div[6]',
                    True,
                    1,
                )
            # Game ended
            except TimeoutException:
                self.running = False

        self.save('//*[@id="root"]/div/div[4]/div[1]/div/div[1]/div/div[3]/button[1]')

    def number_memory(self):
        """Plays the number memory test (https://humanbenchmark.com/tests/number-memory)"""
        # Start the test
        start_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[3]/button', True
        )
        start_element.click()

        while self.running:
            # Get the current number
            number_element = self.wait_for_element(
                '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[1]', False
            )
            number = number_element.text

            # Wait until the number has passed and we can answer
            answer_element = self.wait_for_element(
                '//*[@id="root"]/div/div[4]/div[1]/div/div/div/form/div[2]/input',
                True,
                200,
            )
            # Send the number as the answer
            answer_element.send_keys(number)
            answer_element.send_keys(Keys.ENTER)

            # Start next round
            next_element = self.wait_for_element(
                '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[2]/button', True
            )
            next_element.click()

            # Stop the game when the number gets to 20 digits
            if len(number) == 20:
                self.running = False

        # Kill the bot
        answer_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div/div/form/div[2]/input', True
        )
        # Send incorrect answer
        answer_element.send_keys("end")
        answer_element.send_keys(Keys.ENTER)

        self.save('//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[2]/div/button[1]')

    def verbal_memory(self):
        """Plays the verbal memory test (https://humanbenchmark.com/tests/verbal-memory)"""
        # Start the test
        start_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[4]/button', True
        )
        start_element.click()

        # Buttons to interact with the test
        seen_button = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[3]/button[1]', True
        )
        new_button = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[3]/button[2]', True
        )
        seen_words = []
        score = 0

        while self.running:
            # Get the current word
            word_element = self.wait_for_element(
                '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[2]/div', False
            )
            word = word_element.text

            # Answer whether it's new or seen
            if word in seen_words:
                seen_button.click()
            else:
                new_button.click()
                # In case it's new, store it since we've now seen it
                seen_words.append(word)
            score += 1

            # End the game at 1000 score
            if score == 1000:
                self.running = False
                while True:
                    try:
                        # Say all words are seen until we lose
                        seen_button.click()
                    except StaleElementReferenceException:
                        break

        self.save('//*[@id="root"]/div/div[4]/div[1]/div/div/div[3]/button[1]')

    def chimp(self):
        """Plays the chimp test (https://humanbenchmark.com/tests/chimp)"""
        # Start the test
        start_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div[1]/div[2]/button', True
        )
        start_element.click()

        # Wait until number cards have loaded
        cards_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div[1]/div', False
        )

        # The starting amount of numbers
        num_of_cards = 4

        while self.running:
            # Get all card rows
            rows = []
            # The game consists of 6 rows of cards
            for i in range(1, 6):
                rows.append(
                    self.wait_for_element(
                        f'//*[@id="root"]/div/div[4]/div[1]/div/div[1]/div/div/div[{i}]',
                        False,
                    )
                )

            # Get list of all squares in each row
            cards = [row.find_elements_by_xpath(f".//*") for row in rows]
            clicks = {}

            # Find which cards need to be clicked
            for row_index, row in enumerate(cards):
                for card_index, card in enumerate(row):
                    # Empty card slot
                    if not card or not card.text:
                        continue

                    # Store the card index for clicking later
                    clicks[int(card.text)] = (row_index, card_index)

            # Reload the cards cause their elements have reloaded
            rows = []
            for i in range(1, 6):
                rows.append(
                    self.wait_for_element(
                        f'//*[@id="root"]/div/div[4]/div[1]/div/div[1]/div/div/div[{i}]',
                        False,
                    )
                )

            cards = [row.find_elements_by_xpath(f".//*") for row in rows]

            # Click all cards
            for i in range(1, num_of_cards + 1):
                element_location = clicks[i]
                cards[element_location[0]][element_location[1]].click()

            num_of_cards += 1

            # Continue to the next level
            continue_element = self.wait_for_element(
                '//*[@id="root"]/div/div[4]/div[1]/div/div[1]/div[3]/button', True
            )
            continue_element.click()

            # The game ends at 41 cards
            if num_of_cards == 41:
                self.running = False

        self.save('//*[@id="root"]/div/div[4]/div[1]/div/div[1]/div[3]/button')

    def memory(self):
        """Plays the visual memory test (https://humanbenchmark.com/tests/memory)"""
        # Start the test
        start_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[2]/button', True
        )

        start_element.click()

        # Wait until squares are loaded
        squares_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[2]/div', False
        )

        level = 0
        rows = []
        active_squares = []

        while self.running:
            # Get rows of squares
            rows = self.get_memory_rows(level)
            active_squares = []

            # Wait until all squares in the current level have been flipped, and save their indexes in a list
            while len(active_squares) != level + 2:
                rows = self.get_memory_rows(level)
                active_squares = self.get_memory_active_squares(rows)

            # Wait until all squares have been reflipped
            while len(self.get_memory_active_squares(rows)) != 0:
                rows = self.get_memory_rows(level)

            # Finish the test at level 40
            if level == 40:
                # Make all squares active in order to click wrong squares and lose
                active_squares = [
                    (rows.index(a), b) for a in rows for b in range(len(a))
                ]
                self.running = False

            # Click all active squares
            for row_index, square_index in active_squares:
                rows[row_index][square_index].click()

            level += 1

        # Suicide - end the test
        while True:
            time.sleep(3)
            try:
                # Click the wrong squares until the game as ended
                for row_index, square_index in active_squares:
                    rows[row_index][square_index].click()
            except StaleElementReferenceException:
                break

        self.save('//*[@id="root"]/div/div[4]/div[1]/div/div/div[3]/button[1]')

    def get_memory_rows(self, level):
        """Returns all rows of squares in the memory test"""
        rows = []
        # Rough calculation for num of rows
        row_num = 4 + level // 3
        for i in range(1, row_num):
            squares = []
            for j in range(1, row_num):
                try:
                    squares.append(
                        self.browser.find_element_by_xpath(
                            f'//*[@id="root"]/div/div[4]/div[1]/div/div/div/div[2]/div/div[{i}]/div[{j}]'
                        )
                    )
                # Square doesn't exist (wrong amount of rows)
                except NoSuchElementException:
                    break
            rows.append(squares)
        return rows

    def get_memory_active_squares(self, rows):
        """Get all square indices of squares which are flipped (active) and will need to be clicked in the memory test"""
        squares = []
        for row_index, row in enumerate(rows):
            for square_index, square in enumerate(row):
                if "active" in square.get_attribute("class"):
                    squares.append((row_index, square_index))
        return squares

    def typing(self):
        # Wait for page to load the text we need to type
        text_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div[1]/div/div[2]/div', False
        )

        # Get all letters we need to type
        letters = [
            letter.text if letter.text else " "
            for letter in text_element.find_elements_by_xpath(".//*")
        ]

        # Instantly type the text in the site
        text_element.send_keys("".join(letters))

        # Make it appear as if the bot is typing
        """for letter in letters:
            if not letter:
                letter = " "
            letters_element.send_keys(letter)"""

        self.save('//*[@id="root"]/div/div[4]/div[1]/div/div[3]/button[1]')

    def save(self, xpath: str):
        """Saves the test score"""
        save_element = self.wait_for_element(xpath, True)
        save_element.click()

    def get_games(self):
        """Stores all human benchmark games featured in the homepage"""
        # Open the homepage
        self.browser.get("https://humanbenchmark.com/")

        # Wait for the games elements to appear on screen
        games_element = self.wait_for_element(
            f'//*[@id="root"]/div/div[4]/div[2]/div[2]', False
        )

        # Find all games
        tests = [
            test.get_attribute("href")
            for test in games_element.find_elements_by_xpath(".//*//*")
            if test.get_attribute("href")
        ]

        # Store games in dictionary
        for test_link in tests:
            self.games[test_link.split("/")[-1]] = test_link

    def login(self):
        """Log the bot into the site"""
        with open("./acc-details.json", "r") as details_file:
            acc_details = json.load(details_file)

        # Open login page
        self.browser.get("https://humanbenchmark.com/login")

        # Enter username
        username_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div/div/form/p[1]/input', True
        )
        username_element.send_keys(acc_details["username"])

        # Enter password
        password_element = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div/div/form/p[2]/input', True
        )
        password_element.send_keys(acc_details["password"])

        # Finish login
        submit_button = self.wait_for_element(
            '//*[@id="root"]/div/div[4]/div/div/form/p[3]/input', True
        )
        submit_button.click()

        # Give the site time to log the bot in
        time.sleep(1)

    def wait_for_element(self, path, clickable, timeout=20):
        """Waits for an element by it's xpath"""
        return WebDriverWait(self.browser, timeout).until(
            EC.element_to_be_clickable((By.XPATH, path))
            if clickable
            else EC.presence_of_element_located((By.XPATH, path))
        )


if __name__ == "__main__":
    bot = BenchmarkBot()
    bot.main()

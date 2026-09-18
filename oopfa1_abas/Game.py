from time import time
from Novice import Novice
from Swordsman import Swordsman
from Archer import Archer
from Magician import Magician
from Boss import Boss
import random

class mode_Select():
    def __init__(self):
        self.mode = input("Select a mode: \n1. Multiplayer \n2. Single Player \n")
        if self.mode == "1":
            self.multiplayer()
        elif self.mode == "2":
            self.singleplayer()

    def character_select(self):
        self.player1_name_input = input("Enter name for Player 1: ")
        self.player1class_input = input("1. Swordsman \n2. Archer \n3. Magician\n")
        self.player2_name_input = input("Enter name for Player 2: ")
        self.player2class_input = input("1. Swordsman \n2. Archer \n3. Magician\n")

        if self.player1class_input == "1":
            self.player1 = Swordsman(self.player1_name_input)
        elif self.player1class_input == "2":
            self.player1 = Archer(self.player1_name_input)
        elif self.player1class_input == "3":
            self.player1 = Magician(self.player1_name_input)

        if self.player2class_input == "1":
            self.player2 = Swordsman(self.player2_name_input)
        elif self.player2class_input == "2":
            self.player2 = Archer(self.player2_name_input)
        elif self.player2class_input == "3":
            self.player2 = Magician(self.player2_name_input)

    def multiplayer(self):
        self.character_select()
        print(f"\nGame starts with {self.player1.getUsername()} (HP: {self.player1.getHp()}) vs {self.player2.getUsername()} (HP: {self.player2.getHp()})")

        # Randomly decide who goes first
        players = [self.player1, self.player2]
        random.shuffle(players) # Shuffle to get a random order
        current_player = players[0]
        other_player = players[1]

        turn_count = 0
        while self.player1.getHp() > 0 and self.player2.getHp() > 0:
            turn_count += 1
            print(f"\n--- Turn {turn_count} ---")
            print(f"{current_player.getUsername()}'s turn.")
            print(f"{self.player1.getUsername()} HP: {self.player1.getHp()}")
            print(f"{self.player2.getUsername()} HP: {self.player2.getHp()}")

            self.attack_phase(current_player, other_player)

            # Check if game ended after attack
            if other_player.getHp() <= 0:
                print(f"--- GAME OVER ---")
                print(f"{current_player.getUsername()} wins!")
                break # Exit the while loop

            # Swap players for the next turn
            current_player, other_player = other_player, current_player

        if self.player1.getHp() <= 0 and self.player2.getHp() <= 0:
            print("--- GAME OVER ---")
            print("It's a draw!")
        elif self.player1.getHp() <= 0:
            print("--- GAME OVER ---")
            print(f"{self.player2.getUsername()} wins!")
        elif self.player2.getHp() <= 0:
            print("--- GAME OVER ---")
            print(f"{self.player1.getUsername()} wins!")


    def attack_phase(self, attacker, defender):
        actions = attacker.get_actions()

        print(f"\n{attacker.getUsername()}, what will you do?")
        for i, (name, _) in enumerate(actions, 1):
            print(f"{i}, {name}")

        while True:
            choice = input("Selection: ")
            if choice.isdigit() and 1 <= int(choice) <= len(actions):
                action_name, action_func = actions[int(choice) - 1]

                action_func() if action_name == 'Heal' else action_func(defender)
                break
            print("Invalid choice, try again.")

    def singleplayer(self):
        self.player1 = Novice("Player1")
        self.npc = Boss("NPC_Boss")
        self.start_singleplayer()

    def start_singleplayer(self):
        pass

class Game():
    def __init__(self):
        self.mode = mode_Select()

game = Game()
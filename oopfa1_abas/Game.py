from Novice import Novice
from Swordsman import Swordsman
from Archer import Archer
from Magician import Magician
from Boss import Boss
import random
import time

class Game:
    def __init__(self):
        self.player1 = None
        self.player2 = None
        self.mode_select()

    def mode_select(self):
        mode = input("==========\nSelect a mode:\n1. Multiplayer\n2. Singleplayer\n==========\nChoice: ")
        if mode == "1":
            self.multiplayer()
        elif mode == "2":
            self.singleplayer()


    def create_player(self, player_number):
        name = input(f"Enter a name for Player {player_number}: ")
        print("==========\nSelect a class:\n1. Swordsman\n2. Archer\n3. Magician\n==========")

        while True:
            choice = input("Choice: ")
            if choice in self.CLASSES:
                return self.CLASSES[choice](name)
            print("Invalid selection, pick 1, 2, or 3.")

    CLASSES = {
        "1": Swordsman,
        "2": Archer,
        "3": Magician
    }

    def character_select(self):
        self.player1 = self.create_player(1)
        self.player2 = self.create_player(2)


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

    def evolve_character(self):
        print("\n*The Divine are looking down upon ye...*")
        print("*Great warrior, the time has come to go beyond thyself...*\n*IT IS TIME FOR EVOLUTION!*")
        print("Your Novice limits are breaking! It's time to EVOLVE!")
        print("==========\nSelect your Evolution:\n1. Swordsman\n2. Archer\n3. Magician\n==========")
        
        while True:
            choice = input("Choice: ")
            if choice in self.CLASSES:
                # Store the original name
                player_name = self.player1.getUsername()
                
                # Replace player1 with the newly instantiated class (resets HP to max)
                self.player1 = self.CLASSES[choice](player_name)
                
                print(f"Full HP Restored! You have evolved into a {self.player1.__class__.__name__}!")
                print(f"Current HP: {self.player1.getHp()}")
                break
            print("Invalid selection, pick 1, 2, or 3.")

    def singleplayer(self):
        self.player1 = Novice(input("Enter a name: "))
        self.npc = Boss("Primordial Demon GOD of ELECs; Destroyer of Scholars and Trees; The KIDSMayker; Chika Minute Host; Vaugeposting Plague Guard; Author of Alamat ni Alimunimuni; Owner of Alimunimuni Collection; Alimunimuni Aluminum Foil")
        print(f"\nA terrifying Boss, {self.npc.getUsername()}, blocks your path!")
        time.sleep(1.5)

        turn_count = 0
        while self.player1.getHp() > 0 and self.npc.getHp() > 0:
            turn_count += 1
            if turn_count == 3 and self.player1.__class__.__name__ == "Novice":
                self.evolve_character()
                time.sleep(1.5)

            print(f"\n========== Turn {turn_count} ==========")
            print(f"[ {self.player1.getUsername()} HP: {self.player1.getHp()} | {self.npc.getUsername()} HP: {self.npc.getHp()} ]")
            
            self.attack_phase(self.player1, self.npc)
            time.sleep(1.5)

            #Check if Boss died
            if self.npc.getHp() <= 0:
                print(f"========== GAME OVER ==========")
                print(f"{self.npc.getUsername()} has been defeated! You win!")
                break
                
            #Boss turn
            self.npc.boss_turn(self.player1)
            time.sleep(1.5)
            
            # Check if Player died
            if self.player1.getHp() <= 0:
                print(f"========== GAME OVER ==========")
                print(f"You were struck down by {self.npc.getUsername()}... Game Over.")
                break

    def multiplayer(self):
            self.character_select()

            # Randomly decide who goes first
            players = [self.player1, self.player2]
            random.shuffle(players) # Shuffle to get a random order
            current_player, other_player = players

            # Announce the match with whoever actually won the turn order first
            print(f"\nGame starts with {current_player.getUsername()} (HP: {current_player.getHp()}) vs {other_player.getUsername()} (HP: {other_player.getHp()})")

            time.sleep(1.5)

            turn_count = 0
            while True:
                turn_count += 1
                print(f"\n========== Turn {turn_count} ==========")
                print(f"{current_player.getUsername()}'s turn.")
                print(f"{self.player1.getUsername()} HP: {self.player1.getHp()}")
                print(f"{self.player2.getUsername()} HP: {self.player2.getHp()}")

                self.attack_phase(current_player, other_player)
                time.sleep(1.5)

                # Check for game over state
                if other_player.getHp() <= 0:
                    time.sleep(1)
                    print(f"========== GAME OVER ==========")
                    print(f"{current_player.getUsername()} wins!")
                    break

                # Swap players for the next turn
                current_player, other_player = other_player, current_player

if __name__ == "__main__":
    game = Game()

from Character import Character
import random

class Novice(Character):
    def basicAttack(self, character):
        character.reduceHp(self.getDamage())
        print(f"==========\n{self.getUsername()} performed Basic Attack! -{self.getDamage()}HP\n==========")

    def get_actions(self):
        return[("Basic Attack", self.basicAttack)] #This adds the basic attack to any child of this class

    def roll_d20(self):#Moved the rolling function here in the parent instead.
        roll = random.randint(1, 20)

        if roll == 20:
            return roll, 2.0, "CRIT"
        elif roll >= 15:
            return roll, 1.5, "GREAT"
        elif roll >= 6:
            return roll, 1.0, "HIT"
        elif roll >= 2:
            return roll, 0.5, "GLANCING"
        else:
            return roll, -0.5, "BACKFIRE"
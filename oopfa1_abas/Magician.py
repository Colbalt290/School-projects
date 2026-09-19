from Novice import Novice
import random

class Magician(Novice):
    def __init__(self,username):
        super().__init__(username)
        self.setInt(10)
        self.setVit(5)
        self.setMana(self.getMana() + self.getInt()) #Mana limiter for the Magician, gives the class 60 Mana
        self.setHp(self.getHp() + self.getVit())

    def heal(self): #Uses Mana to heal
        mana_cost = 25
        if self.getMana() >= mana_cost:
            self.setMana(self.getMana() - mana_cost)
            self.addHp(self.getInt())
            print(f"==========\n{self.getUsername()} performed Heal! +{self.getInt()} HP | ({self.getMana()} MP left)\n==========")
        else:
            print(f"==========\n{self.getUsername()} tried to heal, but is out of MP!\n==========")

    def magicAttack(self, character):#Took out the d20 rolling function and gave it to the parent, applied to other classes too.
        mana_cost = 15
        if self.getMana() < mana_cost:
            print(f"==========\n{self.getUsername()} tried to cast Magic Attack, but does not have enough Mana! ({self.getMana()}/{mana_cost} MP)\n==========")
            return

        self.setMana(self.getMana() - mana_cost)

        roll, multiplier, outcome = self.roll_d20()
        base_damage = self.getDamage() + random.randint(2, self.getInt() + 6)

        flavor_texts = {#Randomized text for different dice rolls.
            "BACKFIRE": [
                f"CRITICAL MISS! {self.getUsername()}'s wand exploded!",
                f"YEOUCH!!!! {self.getUsername()}'s spell backfired!"
            ],
            "CRIT":[
                "||MAGIC ATTACK|| NAT 20! OBLITERATING BLOW!!!!",
                "||MAGIC ATTACK|| NAT 20! X-BLAST!!!",
                "||MAGIC ATTACK|| NAT 20! SEPARADE!!!"
            ],
            "GREAT":[
                f"||MAGIC ATTACK|| GREAT HIT!! (Rolled a {roll}) A Magical Hit!",
                f"||MAGIC ATTACK|| GREAT HIT!! (Rolled a {roll}) A Hit filled with Magic!"
            ],
            "HIT":[
                f"||MAGIC ATTACK|| HIT! (Rolled a {roll}) That must've singed their clothes!",
                f"||MAGIC ATTACK|| HIT! (Rolled a {roll}) Aim higher next time!"
            ],
            "GLANCING":[
                f"||MAGIC ATTACK|| Is that it? Can't you do better than that? (Rolled a {roll})",
                f"||MAGIC ATTACK|| Touchy ahh strike. 🥀🥀🥀 (Rolled a {roll})",
                f"||MAGIC ATTACK|| A hit is a hit I guess. 🥀🥀🥀 (Rolled a {roll})",
            ]
        }

        chosen_text = random.choice(flavor_texts[outcome])
        if outcome == "BACKFIRE":#Only happens when we hit a one
            self_damage = int(base_damage * multiplier)
            self.reduceHp(self_damage)
            print(f"==========\n{chosen_text}\nAnd took {self_damage} points of self-damage!")
            return

        final_damage = int(base_damage * multiplier)
        character.reduceHp(final_damage)#Targets enemy!

        print(f"==========\n{chosen_text}\n")
        print(f"Dealt {final_damage} damage to {character.getUsername()}! ({self.getMana()} MP remaining)\n==========")


    def get_actions(self):
        actions = super().get_actions()
        actions.extend([("Magic Attack", self.magicAttack), ("Heal", self.heal)])
        #Uses .extend instead of .append to prevent nested lists in order to print them cleanly onto the terminal
        return actions
    
    
from Novice import Novice
import random

class Archer(Novice):
    def __init__(self,username):
        super().__init__(username)
        self.setStr(5)
        self.setInt(5)
        self.setVit(5)
        self.setHp(self.getHp() + self.getVit())

    def rangedAttack(self, character):
        base_damage = self.getDamage() + self.getStr()
       
        roll, multiplier, outcome = self.roll_d20()

        flavor_texts = {#Copied over from Magician
            "BACKFIRE": [
                f"CRITICAL MISS!!!! {self.getUsername()}'s arrow fell on their knee!",
                f"YEOUCH!!!! {self.getUsername()}'s bowstring snapped back on their face!",
                f"OWIE!!!! {self.getUsername()}'s stomach started grumbling!"
            ],
            "CRIT":[
                "||RANGED ATTACK|| NAT 20! OBLITERATING BLOW!!!!",
                "||RANGED ATTACK|| NAT 20! X-BLAST!!!",
                "||RANGED ATTACK|| NAT 20! SEPARADE!!!"
            ],
            "GREAT":[
                f"||RANGED ATTACK|| GREAT HIT!! (Rolled a {roll}) Right on the lungs!",
                f"||RANGED ATTACK|| GREAT HIT!! (Rolled a {roll}) Right on the spleen!",
                f"||RANGED ATTACK|| GREAT HIT!! (Rolled a {roll}) Right on the chest!"
            ],
            "HIT":[
                f"||RANGED ATTACK|| HIT! (Rolled a {roll})",
                f"||RANGED ATTACK|| HIT! (Rolled a {roll}) It hit them on the knee!"
            ],
            "GLANCING":[
                f"||RANGED ATTACK|| Is that it? Can't you do better than that? (Rolled a {roll})",
                f"||RANGED ATTACK|| Touchy ahh strike. 🥀🥀🥀 (Rolled a {roll})",
                f"||RANGED ATTACK|| A hit is a hit I guess. 🥀🥀🥀 (Rolled a {roll})",
                f"||RANGED ATTACK|| The arrow barely grazed them. 🥀🥀🥀 (Rolled a {roll})"
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
        print(f"Dealt {final_damage} damage to {character.getUsername()}!\n==========")
        

    def get_actions(self):
        actions = super().get_actions()
        actions.append(("Ranged Attack", self.rangedAttack)) #This adds the archer's ranged attack
        return actions
    

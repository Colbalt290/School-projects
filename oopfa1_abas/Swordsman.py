from Novice import Novice
import random

class Swordsman(Novice):
    def __init__(self,username):
        super().__init__(username)
        self.setStr(5)
        self.setVit(15)
        self.setHp(self.getHp() + self.getVit())
        self.max_hp = self.getHp() # Saves maximum HP for passive rage threshold

    def slashAttack(self, character):

        base_damage = self.getDamage() + self.getStr()

        # PASSIVE RAGE: Triggers 50% bonus base damage when HP drops to 50% or lower
        if self.getHp() <= (self.max_hp / 2):
            print(f"\n💢 RAGE PASSIVE ACTIVE! {self.getUsername()}'s low health unleashes extra power!")
            base_damage = int(base_damage * 2.0)

        roll, multiplier, outcome = self.roll_d20()

        flavor_texts = {#Copied over from Magician
            "BACKFIRE": [
                f"CRITICAL MISS!!!! {self.getUsername()}'s pommel hit their stomach!",
                f"YEOUCH!!!! {self.getUsername()} tripped and fell!",
                f"OWIE!!!! {self.getUsername()}'s stomach started grumbling!"
            ],
            "CRIT":[
                "||SLASH ATTACK|| NAT 20! OBLITERATING BLOW!!!!",
                "||SLASH ATTACK|| NAT 20! X-BLAST!!!",
                "||SLASH ATTACK|| NAT 20! SEPARADE!!!"
            ],
            "GREAT":[
                f"||SLASH ATTACK|| GREAT HIT!! (Rolled a {roll}) Right on the lungs!",
                f"||SLASH ATTACK|| GREAT HIT!! (Rolled a {roll}) Right on the spleen!",
                f"||SLASH ATTACK|| GREAT HIT!! (Rolled a {roll}) Right on the chest!"
            ],
            "HIT":[
                f"||SLASH ATTACK|| HIT! (Rolled a {roll}) A solid strike!",
                f"||SLASH ATTACK|| HIT! (Rolled a {roll}) It gashed them!"
            ],
            "GLANCING":[
                f"||SLASH ATTACK|| Is that it? Can't you do better than that? (Rolled a {roll})",
                f"||SLASH ATTACK|| Touchy ahh strike. 🥀🥀🥀 (Rolled a {roll})",
                f"||SLASH ATTACK|| A hit is a hit I guess. 🥀🥀🥀 (Rolled a {roll})",
                f"||SLASH ATTACK|| The sword barely grazed them. 🥀🥀🥀 (Rolled a {roll})"
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
        actions.append(("Slash Attack", self.slashAttack)) #This adds the swordsman's slash attack
        return actions
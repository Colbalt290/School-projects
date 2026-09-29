#Component Primary Parent Class
class component():
    def __init__(self, name, desc):
        self.__name = name
        self.__desc = desc

    def getName(self):
        return self.__name
    def setName(self, new_name):
        self.__name = new_name

    def getDescription(self):
        return self.__desc
    def setDescription(self, new_desc):
        self.__desc = new_desc


#Resistor Child Class
class resistor(component):
    def __init__(self, name, desc, value):
        super().__init__(name, desc)
        self.__value = value

    def setValue(self, new_value):
        self.__value = new_value
    def getValue(self):
        return self.__value


#Circuit Class
class circuit():
    def __init__(self, cnType):
        self.__cnType = cnType
        self.__components = []

    def add_component(self, component):
        self.__components.append(component)

    def compute(self):
        #Return 0 if no components have been added yet
        if not self.__components:
            return 0

        #Series Calculation: R_total = R1 + R2 + ... + Rn
        if self.__cnType.lower() == "series":
            total_resistance = 0
            for component in self.__components: #This for loop constantly adds all known resistors in the series circuit.
                total_resistance += component.getValue()
            return total_resistance

        #Parallel Calculation: 1/R_total = (1/R1) + (1/R2) + ... + (1/Rn)
        elif self.__cnType.lower() == "parallel":
            reciprocal_sum = 0
            for component in self.__components:
                val = component.getValue()
                if val == 0:
                    raise ValueError("Cannot calculate parallel resistance with a 0 Ohm Resistor.")
                reciprocal_sum += 1 / val
            return 1 / reciprocal_sum

        else:
            raise ValueError(f"Invalid connection type: '{self.__cnType}'. use 'series' or 'parallel'.")


#Test Series Circuit
series_circuit = circuit("series")
series_circuit.add_component(resistor("R1", "Resistor 1", 22))
series_circuit.add_component(resistor("R2", "Resistor 2", 10))
series_circuit.add_component(resistor("R3", "Resistor 3", 5))
series_circuit.add_component(resistor("R4", "Resistor 4", 2))

print("Series Total Resistance:", series_circuit.compute())  #Output: 39


#Test Parallel Circuit
parallel_circuit = circuit("parallel")
parallel_circuit.add_component(resistor("R1", "Resistor 1", 7))
parallel_circuit.add_component(resistor("R2", "Resistor 2", 5))
parallel_circuit.add_component(resistor("R3", "Resistor 3", 12))

print("Parallel Total Resistance:", round(parallel_circuit.compute(), 2))  #Output: ~2.3
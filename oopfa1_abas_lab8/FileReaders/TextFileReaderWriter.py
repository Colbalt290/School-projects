
class FileReaderWriter():
  def read(self):
    print("This is the default read method")
  
  def write(self):
    print("This is the default write method")

class TxtFileReaderWriter(FileReaderWriter):
  def read(self, filepath):
    with open(filepath, "r") as read_file:
      data = read_file.read()
      print(data)
      return data
  
  def write(self, filepath, data):
    with open(filepath, "w") as write_file:
      write_file.write(data)

df = FileReaderWriter()
df.read()
df.write()

txt = TxtFileReaderWriter()
txt.read("oopfa1_abas_lab8/example.txt")
txt.write("oopfa1_abas_lab8/example.txt", "This is a test. I've accepted this test to stand victorious against my past. A person grows once they are able to defeat their weaker self. Wouldn't you agree, Jean Pierre Polnareff?")
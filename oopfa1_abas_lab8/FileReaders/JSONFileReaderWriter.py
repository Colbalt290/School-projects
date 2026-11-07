from oopfa1_abas_lab8.FileReaders.FileReaderWriter import FileReaderWriter
import json

class JSONFileReaderWriter(FileReaderWriter):
  def read(self, filepath):
    with open(filepath, "r") as read_file:
      data = json.load(read_file)
      print(data)
      return data
  
  def write(self, filepath, data):
    with open(filepath, "w") as write_file:
      json.dump(obj=data, fp=write_file)
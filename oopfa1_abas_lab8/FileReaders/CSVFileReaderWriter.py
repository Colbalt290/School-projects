from oopfa1_abas_lab8.FileReaders.FileReaderWriter import FileReaderWriter
import csv

class CSVFileReaderWriter(FileReaderWriter):
  def read(self, filepath):
    with open(filepath, newline='') as csvfile:
      data = csv.reader(csvfile, delimiter=',', quotechar='|')
      for row in data:
        return data

  def write(self, filepath, data):
    with open(filepath, 'w', newline='') as csvfile:
      writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
      writer.writerow(data)
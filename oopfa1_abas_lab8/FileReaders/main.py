from oopfa1_abas_lab8.FileReaders.FileReaderWriter import FileReaderWriter
from oopfa1_abas_lab8.FileReaders.CSVFileReaderWriter import CSVFileReaderWriter
from oopfa1_abas_lab8.FileReaders.JSONFileReaderWriter import JSONFileReaderWriter

# Test the default class
df = FileReaderWriter()
df.read()
df.write()

# Test the polymorphed methods
c = CSVFileReaderWriter()
c.read("sample.csv")
c.write("sample.csv", data=["Hello", "World"])

j = JSONFileReaderWriter()
j.read("sample.json")
j.write(data=['foo', {'bar': ('baz', None, 1.0, 2)}], filepath="sample2.json")
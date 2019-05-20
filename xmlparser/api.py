from .parser import XMLParser

def xml_to_csv(specs_json_path, write_to_file=True, output_dir=None):
    xp = XMLParser(specs_json_path, write_to_file=write_to_file, output_dir=output_dir)
    xp.xml_to_csv()

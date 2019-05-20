# xmlparser
A simple xml parser which is driven by a config.

If you have an xml with multiple parent/children hierarchy records and want to import it into a csv or just view in a readable format, this is the api to go-to. There is also support for namespace in xml. All the data needs to be input in the specs and voila !

Here is an example usage,

```python
from xmlparser import xml_to_csv

spec_json_path = "path/to/spec/json"
xml_to_csv(spec_json_path)
```
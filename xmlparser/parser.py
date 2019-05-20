import os
import csv
from pathlib import Path
from lxml import etree as ET
from .utils import file_exists, path_exists, load_json_from_path, get_current_timestamp_as_str, write_to_csv, pretty_print_records

ROOT = "root"
PARENT = "parent"
INPUT_FILE = "input_file"
DEFAULT_SPEC_FILE_NAME = "specs.json"
TAG_NAME = "tag_name"
CHILDREN = "children"
NAME = "name"
START_FROM = "start_from"
MAX_COUNT = "max_count"
NAMESPACE = "namespace"
XPATH = "xpath"
FILTER = "filter"

class XMLParser(object):

    def __init__(self, specs_json_path, write_to_file=True, output_dir=None):
        self.specs_json_path = specs_json_path
        self.write_to_file = write_to_file
        self.output_dir = output_dir or self._guess_dir()
        self._assert_input_params()
        self.input_file = None
        self.specs_dict = self._load_json() 
        self._validate_specs()
        self.input_file = self.specs_dict.get(INPUT_FILE)
    
    def _assert_input_params(self):
        if not self.specs_json_path:
            raise ValueError("specs_json_path is mandatory")
        if not path_exists(self.specs_json_path):
            raise ValueError("specs_json_path should be a valid path")
        if self.write_to_file: 
            if not self.output_dir:
                raise ValueError("output_dir is mandatory")
            if not path_exists(self.output_dir):
                raise ValueError("output_dir should be a valid path")
    
    def _load_json(self):
        #handle directory.Assuming specs.json as default spec file name
        if file_exists(self.specs_json_path):
            spec_json_path = self.specs_json_path
        else:
            if path_exists(self.specs_json_path):
                spec_json_path = os.path.join(self.specs_json_path, DEFAULT_SPEC_FILE_NAME)
            else:
                raise ValueError("spec_json_path should be a valid path to spec json file or valid directory to where specs.json exists")
        json_ = {}
        try:
            json_ = load_json_from_path(spec_json_path)
        except:
            raise ValueError("spec_json_path should be a valid path to spec json file or valid directory to where specs.json exists")
        return json_
    
    def _validate_specs(self):
        root = self.specs_dict.get(ROOT) or {}
        input_file = self.specs_dict.get(INPUT_FILE)
        parent = None
        if root:
            parent = root.get(PARENT)
        if not all([root, parent, input_file]):
            raise ValueError("input_file, root and parent are mandatory tags in specs_json")
        if not file_exists(input_file):
            raise ValueError("input_file - " + str(input_file) + " not found")

    def _guess_dir(self):
        home = str(Path.home())
        curr_dir = os.path.abspath(os.curdir)
        path_ = home or curr_dir
        return path_
    
    def xml_to_csv(self):
        parents = self.specs_dict[ROOT][PARENT]
        start = 1
        for parent in parents:
            children = parent.get(CHILDREN)
            if not children:
                continue
            self._assert_key(parent, TAG_NAME, "Parent tag_name")
            parent_tag = parent[TAG_NAME]
            header, output_csv_records = self._parse_children(parent_tag, children)
            if self.write_to_file:
                output_filename = parent.get(NAME) or parent.get(TAG_NAME)
                if not output_filename:
                    output_filename = str(start)
                    start += 1
                output_filename = output_filename + "_" + get_current_timestamp_as_str() + ".csv"
                output_path = os.path.join(self.output_dir, output_filename)
                write_to_csv(output_csv_records, header, output_path)
            else:
                pretty_print_records(output_csv_records)

    
    def _parse_children(self, parent_tag, children):
        start_from = self.specs_dict.get(START_FROM, 1) - 1
        max_count = self.specs_dict.get(MAX_COUNT, -1)
        ns = self.specs_dict.get(NAMESPACE)
        count = 0
        header = self._get_children_tags(children)
        output_csv_records = []
        for event, element in ET.iterparse(self.input_file, self._namespaced_path(ns, parent_tag)):
            if((start_from-1) < 0):
                start = 1
                c_text = {}
                filters = {}
                for c in children:
                    text = ""
                    self._assert_key(c, XPATH, "Child xpath")
                    elements = element.findall(self._namespaced_path(ns, str(c[XPATH]).strip()))
                    if elements:
                        texts = self._parse_text(c, elements) or []
                        text = (os.linesep).join(texts)
                    t = self._guess_tag(c)
                    if not t:
                        t = str(start)
                        start += 1
                    c_text[t] = text
                    if c.get(FILTER):
                        filters[t] = c[FILTER]
                if filters:
                    if self._apply_filter(c_text, filters, output_csv_records):
                        count += 1
                else:
                    output_csv_records.append(c_text)
                    count += 1
            start_from -= 1
            if count == max_count:
                break
        return (header, output_csv_records)
    
    def _get_children_tags(self, children):
        result = []
        start = 1
        for child_meta in children:
            t = self._guess_tag(child_meta)
            if not t:
                t = str(start)
                start += 1
            result.append(t)
        return result
    
    def _guess_tag(self, child_meta):
        if not child_meta:
            return
        tag_ = child_meta.get(NAME) or child_meta.get(TAG_NAME)
        if tag_ and tag_.strip():
            return tag_.strip()
        xpath_ = child_meta.get(XPATH)
        if not xpath_:
            return
        xpath_splits = xpath_.split("/")
        for x in xpath_splits[::-1]:
            if str(x).strip().isalnum():
                return str(x).strip()
    
    def _parse_text(self, child, elements):
        max_count = child.get(MAX_COUNT, -1)
        max_count = int(max_count)
        texts = []
        if max_count == 0:
            return texts
        for n, e in enumerate(elements):
            if max_count == n:
                break
            if len(e) > 0:
                sub_element_data = []
                for sub_element in e:
                    tag = ET.QName(sub_element.tag).localname
                    text = sub_element.text or ""
                    if tag:
                        sub_element_data.append(str(tag) + "=" + str(text))
                texts.append(",".join(sub_element_data))
            else:
                t =  e.text or ""
                if t:
                    texts.append(t)
        return texts
    
    def _apply_filter(self, c_text, filters, output_csv_records):
        for k,v in c_text.items():
            if filters.get(k):
                filter_values = filters[k]
                if isinstance(filter_values, (tuple,list)):
                    for value in filter_values:
                        if str(value).strip().lower() == str(v).strip().lower():
                            output_csv_records.append(c_text)
                            return True
                else:
                    value = filter_values.strip()
                    if str(value).strip().lower() == str(v).strip().lower():
                            output_csv_records.append(c_text)
                            return True
        return False
    
    def _namespaced_path(self, ns, path):
        if not path:
            return
        paths = path.split("/")
        namespaced_path = []
        for p in paths:
            np = p
            if ns and str(p).isalnum():
                np = "{" + ns + "}" + p
            namespaced_path.append(np)
        return "/".join(namespaced_path)
            
    def _assert_key(self, obj, key, message=None):
        v = obj.get(key)
        message = message or str(key)
        if v is None:
            raise ValueError(message + " is mandatory")

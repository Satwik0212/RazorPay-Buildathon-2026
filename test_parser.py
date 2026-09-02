import csv
import re
import json

def parse_specs(spec_str):
    if not spec_str or spec_str == '{"product_specification"=>[]}':
        return {}
    
    results = {}
    for match in re.finditer(r'"key"\s*=>\s*"(.*?)",\s*"value"\s*=>\s*"(.*?)"', spec_str):
        results[match.group(1)] = match.group(2)
        
    return results

with open('backend/data/raw/flipkart_com-ecommerce_sample.csv', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for i in range(5):
        row = next(reader)
        print('Original:', row[14])
        print('Parsed:', parse_specs(row[14]))

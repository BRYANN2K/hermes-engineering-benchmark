#!/usr/bin/env python3
import json, sys

def build_plan(manifest):
    # BUG: alphabetical order is not dependency order.
    return sorted(service["name"] for service in manifest["services"])

def main():
    with open(sys.argv[1], encoding="utf-8") as f: manifest=json.load(f)
    print(json.dumps(build_plan(manifest)))
if __name__=="__main__": main()

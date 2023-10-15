import os
import yaml
import json
import csv

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

# vars: str, list, dict
# files: txt, yml, json, csv
# converts: vars2files, file2vars, vars2vars

class Fo:
    # common.is_exist
    @staticmethod
    def d_exist(d): return os.path.isdir(d)
    @staticmethod
    def f_exist(f): return os.path.isfile(f)

    # common.is_empty
    @staticmethod
    def d_empty(d): return False if os.listdir(d) else True
    # TODO: check if file has no content

    # common.fname_split
    @staticmethod
    def dirname(f): return os.path.dirname(f)
    @staticmethod
    def basename(f): return os.path.basename(f)
    # TODO: dir-name split

    # common.f_manupulate
    @staticmethod
    def f_clear(f): open(f, 'w', encoding='utf-8').close()
    def d_create(d): os.mkdir(d)
    @staticmethod
    def add2start(data, f):
        f = open(f,'r+')
        f.seek(0)
        f.write(data)
        [f.write(i) for i in f.readlines()]
        f.close()
        return True
    @staticmethod
    def f_merge(src_files, dest_file):
        with open(dest_file, 'w') as dest:
            for f in src_files:
                with open(f) as infile:
                    [dest.write(i) for i in infile]
        return True

    # vars2vars
    @staticmethod
    def str2dict(s): return yaml.safe_load(s)

    # vars2files
    @staticmethod
    def str2txt(data, f):
        with open(f,'w') as f:
            f.write(data)
    @staticmethod
    def str2txt_append(data, f):
        with open(f, 'a') as f:
            f.write(data + '\n')
    # vars2file: list
    @staticmethod
    def list2txt(data, f):
        with open(f, 'w', encoding='utf-8') as f:
            for item in data:
                f.write("%s\n" % item)
    # def list2yml(data, f)
    @staticmethod
    def list2json(data, f):
        with open(f, 'w') as f:
            f.write(json.dumps(data))
    @staticmethod
    def list2csv(data, f):
        with open(f, 'w', encoding='utf-8') as f:
            w = csv.DictWriter(f, data[0].keys())
            w.writeheader()
            for row in data:
                w.writerow(row)

    # vars2file: dict
    @staticmethod
    def dict2yml(data, f, sort=True, aliases=True):
        with open(f, 'w', encoding='utf-8') as f:
            if aliases:
                yaml.dump(data, f, allow_unicode=True, sort_keys=sort, width=4096)
            else:
                yaml.dump(data, f, allow_unicode=True, sort_keys=sort, width=4096, Dumper=NoAliasDumper)
    @staticmethod
    def dict2json(data, f):
        with open(f, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    # TODO: def dict2csv(data, f)

    # file2vars: txt
    @staticmethod
    def txt2str(f):
        with open(f, 'r') as file:
            return file.read()
    @staticmethod
    def txt2list(f, save_spaces=False):
        if save_spaces:
            lines = []
            with open(f, 'r') as file:
                for line in file:
                    lines.append(line.rstrip())
            return lines
        return [i.strip() for i in open(f).readlines()]
    # file2vars: yml
    # TODO: def yml2list(f)
    @staticmethod
    def yml2dict(f):
        with open(f, encoding='utf-8') as f:
            return yaml.safe_load(f)
    @staticmethod
    def txt2dict(txt):
        return yaml.safe_load(txt)
    # file2vars: json
    @staticmethod
    def json2list(f):
        with open(f, 'r') as f:
            return json.loads(f.read())
    @staticmethod
    def json2dict(f):
        with open(f) as f:
            return json.load(f)
    # file2vars: csv
    @staticmethod
    def csv2list(f):
        data = []
        with open(f, 'r', encoding='utf-8') as f:
            for line in csv.DictReader(f):
                data.append(line)
        return data
    # TODO: def csv2dict(f)

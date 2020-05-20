from itertools import permutations
import argparse
import copy
import sys
import json

VERBOSE = True
VERBOSE = False

DATA = """
name	home	age	team	midname
ag	exmouth	mid	spurs   NULL
tom	exeter	mid	spurs	albert
jake	exeter	mid	spurs	jacob
hattie	exmouth	young	spurs	mary
shep	exeter	old	leicester   NULL
frank	exmouth	old	spurs	wolsten
grace	exmouth	young	spurs	mary
bryn	exmouth	young	spurs	mary
""".strip().split('\n')


def split_line(line, delimiter=','):
    if not delimiter:
        # I.e. None, i.e. white space
        resp = line.strip().split(delimiter)
    else:
        resp = line.strip().replace(' ', '').replace('\t', '').split(delimiter)
    
    return resp
 

def parse_input(fpath, remove_zero_counts=True, delimiter=','):

    with open(fpath) as reader: 
        data = reader.read().strip().split('\n')

    print(f'[INFO] Read in {len(data) - 1} lines.')

    columns = split_line(data[0], delimiter)
 
    if remove_zero_counts: 
        count_column = columns.index('count')

    records = []


    for items in sorted(data[1:]):
        items = split_line(items, delimiter)

        if remove_zero_counts and int(items[count_column]) == 0:
            continue

        records.append({})

        for i in range(len(items)):
            key = columns[i]

            if key == 'domain': 
                continue

            if remove_zero_counts and key == 'count':
                continue

            records[-1][key] = items[i]

    if 'domain' in columns:
        columns.remove('domain')

    if remove_zero_counts and 'count' in columns:
        columns.remove('count')

    print(f'[INFO] Parsed {len(records)} records.')
    return columns, records


def resort_by_keys(key_order, records):
    nr = [[_[key] for key in key_order] for _ in records]
    nr.sort()

    return [dict([(key, [_[i]]) for i, key in enumerate(key_order)]) for _ in nr]



def generate_constraints(key_order, records):

    recs = resort_by_keys(key_order, records)
    constraints = []
    last_rec = [[] for _ in range(len(key_order))]


    if VERBOSE:
        print(f'[INFO] Generating constraints for key order: {key_order}')
    else:
        print('.', end='', flush=True)

    for rec in recs:

        extend = True
        values = []

        for i, key in enumerate(key_order):
            value = rec[key][0]

            if value not in last_rec[i] and i != (len(key_order) - 1):
                extend = False

            values.append([value])

        if extend:
            constraints[-1][key_order[-1]].append(value)

        else:
            new_rec = dict([(key_order[i], values[i]) for i in range(len(key_order))])
            constraints.append(new_rec)

        last_rec = values[:]

    return constraints


def minimise(columns, records):

    key_perms = [_ for _ in permutations(columns)]

    if VERBOSE:
        print(f'[INFO] All key orders:')
        for key_order in enumerate(key_perms):
            print(key_order)

    best = [-1, len(records), None]

    for count, key_order in enumerate(key_perms):
        constraints = generate_constraints(key_order, records)

        if len(constraints) < best[1]:
            print(f'\n[INFO] Length vs best: {len(constraints)} VS {best[1]}')

            best = [count, len(constraints), constraints[:]]

            if VERBOSE:
                for con in constraints: 
                    if ['36'] in con.values():
                        print(f'[DEBUG] Logging presence of variable "36"')

            print(f'[INFO] Length: {len(constraints)} for {key_order}')

    if not best[2]:
        best[2] = records

    return best[2]


def _encode_rec(rec):
    nd = {}

    for k, value in rec.items():
        value = str(value).replace('[', '').replace(']', '').replace(' ', '___')
        nd[k] = value

    return nd


def encode_records(c):
    n = []

    for i in c:
        nd = _encode_rec(i)
        n.append(nd)

    return n


def sort_records(c):
    n = []
    sorted_keys = sorted(c[0].keys())

    c_as_strs = []

    for rec in c:

        r_str = ''
        for key in sorted_keys:
            value = rec[key]
            r_str += f'{key}={value}&'
           
        c_as_strs.append(r_str)

    c_as_strs.sort()

    for rec in c_as_strs:
        d = dict([tuple(_.split('=')) for _ in rec.strip('&').split('&')])
        n.append(d)

    return n


def _decode_rec(rec):
    nd = {}

    for k, value in rec.items():
        if VERBOSE: print(f'[WARN] VALUE IS: {value}', end='  ')

        nv = []

        for _ in value:
            nvalue = eval(_.replace('___', ' ')) 
            nv.append(nvalue)

        if VERBOSE: print(f'decodes to: {nv}')
 
        # Fix when tuple
        if type(nv[0]) == tuple:
            nv = list(nv[0])

        nd[k] = nv

    return nd


def decode_records(c):
    n = []

    for i in c:
        nd = _decode_rec(i)
        n.append(nd)

    return n 


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--verbose', type=bool, default=False,
                        required=False, help='Verbose mode')
    parser.add_argument('-d', '--delimiter', nargs=1, type=str, default=',',
                        required=False, help='Delimiter')
    parser.add_argument('-z', '--remove-zero-counts', type=bool, default=True,
                        required=False, help='Removes records where count is zero')
    parser.add_argument('-i', '--input-file', required=True, nargs=1, help='Input file')
    parser.add_argument('-o', '--output-file', required=True, nargs=1, help='Output file')

    return parser.parse_args()


def set_verbose(verbose):
    global VERBOSE
    VERBOSE = verbose


def main():

    args = parse_args()
    set_verbose(args.verbose)

    print("""
--- ITERATION 0 ---
---------------------
---------------------""")
    # First iteration uses input from file
    columns, records = parse_input(args.input_file[0], remove_zero_counts=args.remove_zero_counts,
                             delimiter=args.delimiter)
    n_recs = len(records)

    print(f'[INFO] Processing {n_recs} records')
    constraints = minimise(columns, records)

    N_ITERATIONS = 200

    for i in range(N_ITERATIONS):
        print(f"""
--- ITERATION {i+1} ---
---------------------
---------------------""")
        
        encoded = encode_records(constraints)
        encoded = sort_records(encoded)

        columns = sorted(encoded[0].keys())

        next_constraints = minimise(columns, encoded)

        if len(next_constraints) < len(constraints):
            print(f'\n[INFO] Minimising from {len(constraints)} to {len(next_constraints)}')
            constraints = copy.deepcopy(decode_records(next_constraints))
        else:
            print(f'\n[INFO] Exiting because lengths are: {len(constraints)} and {len(next_constraints)}')
            break

    print(f'[INFO] Final constraints:')
    total = 0
    for constr in constraints:
        
        n = 1
        for _ in constr.values():
            n *= len(_)

        total += n
        print(f'\tCOUNT: {n}:  {constr}')

    print(f'\n[INFO] Length: {len(constraints)}')
    print(f'[INFO] Record count from file: {len(records)}')
    print(f'[INFO] Record count from minimisation: {total}') 

    json_file = 'constraints.json' 
    with open(json_file, 'w') as writer:
        json.dump(constraints, writer, indent=4)

    print(f'[INFO] Wrote: {json_file}')


if __name__ == '__main__':

    main()

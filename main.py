#!/usr/bin/env python3

import re, json, time, datetime

from urllib import request
from urllib import parse
from argparse import ArgumentParser
from gmpy2 import mpq as Fraction
from config import global_config
from quadratic import Quadratic
from solver.integral import IntegralTchisla
from solver.rational import RationalTchisla
from solver.quadratic import QuadraticTchisla

integral_re = re.compile("^\\d+$")
rational_re = re.compile("^\\d+(/\\d+)?$")
number_re = rational_re

problems_re = re.compile("^(?:\[(?P<targets>[^\]]*)\]|(?P<target>[1-9]\d*(?:\/[1-9]\d*)?))(?:#(?:\[(?P<digits>[^\]]*)\]|(?P<digit>[1-9])))?$")
targets_re = re.compile("^(?:(?P<target>[1-9]\d*(?:\/[1-9]\d*)?)|(?P<start>[1-9]\d*)-(?P<end>[1-9]\d*))$")
digits_re = re.compile("^(?P<first>[1-9])(?:-(?P<last>[1-9]))?$")

solvers = {
    "integral": {
        "regex": integral_re, "constructor": int, "solver": IntegralTchisla
    },
    "rational": {
        "regex": rational_re, "constructor": Fraction, "solver": RationalTchisla
    },
    "quadratic": {
        "regex": rational_re, "constructor": Quadratic, "solver": QuadraticTchisla
    }
}

def submit(target, digits, digits_count, solution):
    print("Submitting {}#{}: {}   {}".format(target, digits, digits_count, solution))
    result_path = "results/results.txt"
    with open(result_path, encoding='utf-8', mode='a') as f:
        f.write("{},{},{},{}\n".format(target, digits, digits_count, solution))

    data = {
        "records_timestamp" : str(int(time.time()) * 1000),
        "app" : "Numbers",
        "app_version" : "1.17",
        "app_family" : 0,
        "results" : [
          {
            "solution" : solution,
            "digits_count" : digits_count,
            "digits" : digits,
            "target" : target,
            "date" : datetime.datetime.utcnow().isoformat() + "+00:00"
          }
        ],
        "os_version" : "9.3.4",
        "lang" : "zh",
        "orientation" : 1,
        "device" : "iPad2,1"
    }

    submit_url = 'http://www.euclidea.xyz/api/v1/game/numbers/solutions'
    req = request.Request(submit_url)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    json_payload = json.dumps(data)
    jsondata = json_payload.encode('utf-8')
    req.add_header('Content-Length', len(jsondata))
    r = request.urlopen(req, jsondata)
    content = json.loads(r.read().decode('utf-8'))
    print(content)

def general_solver(n, target, options):
    max_depth = options.max_depth
    depth = max_depth and max_depth + 1
    if options.check_wr:
        record = fetchRecord(target, n)
        record = int(record['digits_count']) if record else None
        if record:
            depth = record
    solution = None
    for solver_key in options.solvers:
        solver = solvers[solver_key]
        if not solver["regex"].match(str(target)):
            continue
        current_target = solver["constructor"](target)
        tchisla = solver["solver"](n, current_target)
        max_depth = depth
        depth = tchisla.solve(max_depth = max_depth and max_depth - 1)
        if depth is None:
            depth = max_depth
            continue
        if solution:
            print("=" * 20)
        solution = tchisla.solution_prettyprint(current_target, force_print=True)
        for string in solution:
            print(string)
        full_expression = str(tchisla.full_expression(tchisla.target))
        print(current_target, "=", full_expression, flush = True)
        digits_count = tchisla.solutions[current_target][0]
        if options.submit:
            submit(int(current_target), n, digits_count, full_expression)

        if global_config["verbose"]:
            print('\007', end='', flush = True)
    if depth and options.check_wr:
        if not record or record > depth:
            print('New WR Found!', flush = True)

def solve(problem, options):
    print(problem[0], '#', problem[1], flush = True)
    general_solver(problem[1], problem[0], options)

def parse_problems(problems):
    problem_list = set()
    for each in problems:
        m = problems_re.match(each)
        if not m:
            continue

        targets = m.group('targets')
        targets = parse_targets(targets) if targets else [to_number(m.group('target'))]

        digits = m.group('digits')
        digit = m.group('digit')
        digits = parse_digits(digits) if digits else [int(digit)] if digit else list(range(1, 10))

        for target in targets:
            for digit in digits:
                problem_list.add((target, digit))
    problem_list = sorted(problem_list)

    return problem_list

def to_number(string):
    number = Fraction(string)
    if number.denominator == 1:
        number = int(number)
    return number

def parse_digits(digits):
    digit_list = set()
    digits = digits.split(',')
    for each in digits:
        m = digits_re.match(each)
        if not m:
            continue
        first = int(m.group('first'))
        last = m.group('last')
        last = int(last) if last else first
        if first > last:
            first, last = last, first
        digit_list = digit_list | set(range(first, last + 1))
    digit_list = sorted(digit_list)
    return digit_list


def parse_targets(targets):
    target_list = set()
    targets = targets.split(',')
    for each in targets:
        m = targets_re.match(each)
        if not m:
            continue
        target = m.group('target')
        if target:
            target_list.add(to_number(target))
            continue
        start = int(m.group('start'))
        end = int(m.group('end'))
        if start > end:
            start, end = end, start
        target_list = target_list | set(range(start, end + 1))
    target_list = sorted(target_list)
    return target_list

def fetchRecord(target, digit):
    url = 'http://www.euclidea.xyz/api/v1/game/numbers/solutions/records?query=[{},{}]'.format(target, digit)
    r = request.urlopen(url)
    content = json.loads(r.read().decode('utf-8'))
    records = content['records']
    return records[0] if records else None


def main():
    default_solvers = ['integral', 'rational']
    parser = ArgumentParser()
    parser.add_argument('-s', '--add-solver',
        dest='solvers',
        action='append',
        choices=list(solvers.keys()),
        help='set solvers list from empty, add one solver each time, the default set is ' + str(default_solvers)
    )
    parser.add_argument('-d', '--max-depth',
        type=int,
        help='max search depth'
    )
    parser.add_argument('-c', '--check-wr',
        action='store_true',
        default=False,
        help='switch mode to try to find a solution shorter than the current WR',
    )
    parser.add_argument('-u', '--submit',
        action='store_true',
        default=False,
        help='Submit the solution to the Tchisla server',
    )
    parser.add_argument('-v', '--verbose',
        action='store_true',
        default=False,
        help='enable detailed output'
    )
    parser.add_argument('problem',
        nargs='+',
        help='problem to solve, examples: "2", "2#5", "[1,3]#8", "[2-4]#[6,7]", "[3-6,125,127]#[2-9]"'
    )
    options = parser.parse_args()
    global_config["verbose"] = options.verbose
    if not options.solvers:
        options.solvers=default_solvers
    problem_list = parse_problems(options.problem)
    for problem in problem_list:
        solve(problem, options)

if __name__ == "__main__":
    main()

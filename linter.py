import argparse
import os

from glob import glob
import sys
import subprocess
from typing import Optional, Tuple
from pylint.lint import Run


class CodeQualityError(Exception):
    ...


def lint(path: str, threshold: float):
    results = Run(["pyisotools"], do_exit=False)
    score = results.linter.stats["global_note"]

    print(" ".join(["echo", "{PYLINT_COLOR}={red}", ">>", "$GITHUB_ENV"]))
    if results.linter.msg_status & 3:
        subprocess.run(["echo", "{PYLINT_COLOR}={red}", ">>", "$GITHUB_ENV"])
        subprocess.run(["echo", "{PYLINT_VALUE}={failing}", ">>", "$GITHUB_ENV"])
        raise CodeQualityError("Code is erroneous!")

    if score < 3:
        color = "red"
    elif score < 5:
        color = "orange"
    elif score < 7:
        color = "yellow"
    else:
        color = "green"

    subprocess.run(["echo", "{PYLINT_COLOR}="+"{"+color+"}", ">>", "$GITHUB_ENV"])
    subprocess.run(["echo", "{PYLINT_VALUE}="+"{"+str(score)[:4]+"}", ">>", "$GITHUB_ENV"])

    if score < threshold:
        raise CodeQualityError(
            f"Code quality is too poor [{score} < {threshold}]")


def main(args: Optional[Tuple[str]] = None):
    parser = argparse.ArgumentParser(prog="LINT")
    parser.add_argument('path',
                        help='path to directory you want to run pylint | '
                        'Default: %(default)s | '
                        'Type: %(type)s ',
                        type=str)

    parser.add_argument('-t',
                        '--threshold',
                        help='score threshold to fail pylint runner | '
                        'Default: %(default)s | '
                        'Type: %(type)s ',
                        default=7,
                        type=float)

    args = parser.parse_args()
    path = str(args.path)
    threshold = float(args.threshold)

    lint(path, threshold)


main(sys.argv[1:])

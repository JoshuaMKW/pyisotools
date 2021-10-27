import argparse
import os
import subprocess
import sys
from glob import glob
from typing import Optional, Tuple

from actions_toolkit import core
from pylint.lint import Run


class CodeQualityError(Exception):
    ...


def lint(path: str, threshold: float):
    results = Run(["pyisotools"], do_exit=False)
    score = results.linter.stats["global_note"]

    if results.linter.msg_status & 3:
        core.export_variable("PYLINT_COLOR", "red")
        core.export_variable("PYLINT_VALUE", "failing")
        raise CodeQualityError("Code is erroneous!")

    if score < 3:
        color = "red"
    elif score < 5:
        color = "orange"
    elif score < 7:
        color = "yellow"
    else:
        color = "green"

    core.export_variable("PYLINT_COLOR", color)
    core.export_variable("PYLINT_VALUE", score)

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

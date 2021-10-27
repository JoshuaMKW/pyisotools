import sys

from pylint.lint import Run

if __name__ == "__main__":
    result = Run([sys.argv[1], f"--rcfile={sys.argv[2]}"], do_exit=False)
    exitCode = result.linter.msg_status
    rating = result.linter.stats["global_note"]

    if exitCode & 3 or rating < float(sys.argv[3]):
        sys.exit(exitCode)
"""Default execution entry point if running the package via python -m"""
import cd.cli
import sys


def main():
    return cd.cli.main()


if __name__ == '__main__':
    sys.exit(main())

"""Default execution entry point if running the package via python -m"""
import pypyr.cli
import sys


def main():
    return pypyr.cli.main()


if __name__ == '__main__':
    sys.exit(main())

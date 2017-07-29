# -*- coding: utf-8 -*-

"""Console script for sockspy."""

import click
from sockspy import sockspy_main


@click.command()
def main(args=None):
    """Console script for sockspy."""
    click.echo("Starting sockspy...")
    sockspy_main.run()


if __name__ == "__main__":
    main()

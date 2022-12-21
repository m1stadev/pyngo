import sys

import click

import pyngo

from . import __version__


@click.command()
@click.version_option(message=f'Pyngo {__version__}')
@click.option(
    '-c',
    '--command',
    'command',
    type=str,
    required=True,
    help='Command to send.',
)
@click.option(
    '-v',
    '--verbose',
    'verbose',
    is_flag=True,
    help='Increase verbosity.',
)
def main(command: str, verbose: bool) -> None:
    '''A Python CLI tool for decrypting iOS/iPadOS bootchain firmware keys.'''

    if not verbose:
        sys.tracebacklimit = 0

    click.echo('Attempting to connect to device')
    try:
        client = pyngo.Client.init()
    except:
        click.echo('[ERROR] Failed to connect to device. Exiting.')
        return

    click.echo(f'Sending command: {command}')
    click.echo(f'Output:\n{client.send_command(command)}')


if __name__ == '__main__':
    main()

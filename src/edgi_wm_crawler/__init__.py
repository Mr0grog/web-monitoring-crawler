from sys import exit, stderr
from .seeds import active_urls, format_text, format_browsertrix


def main() -> None:
    from argparse import ArgumentParser

    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    seeds_command = subparsers.add_parser('seeds', help='Generate crawler seeds')
    seeds_command.add_argument(
        '--format',
        choices=('text', 'browsertrix'),
        default='text',
        help='Format of seeds output.'
    )
    seeds_command.add_argument(
        '--pattern',
        help='Only list URLs matching this pattern.'
    )
    seeds_command.add_argument(
        '--workers',
        type=int,
        default=4,
        help='How many workers (browserstrix only).'
    )
    seeds_command.set_defaults(func=generate_seeds)

    args = parser.parse_args()
    args.func(**vars(args))


def generate_seeds(*, format, pattern, workers, **_kwargs) -> None:
    print(f'Generating seeds as {format}...', file=stderr)
    urls = active_urls(pattern=pattern)
    if format == 'text':
        print(format_text(urls))
    elif format == 'browsertrix':
        print(format_browsertrix(urls, workers=workers))
    else:
        print(f'Unknown format: "{format}"', file=stderr)
        exit(1)

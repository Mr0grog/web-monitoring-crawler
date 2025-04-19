from itertools import batched
import json
from pathlib import Path
from sys import exit, stderr
from .seeds import active_urls, format_text, format_browsertrix, group_urls


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

    multi_seeds_command = subparsers.add_parser('multi-seeds', help='Generate multiple seed lists of at most `size` URLs')
    multi_seeds_command.add_argument(
        '--format',
        choices=('text', 'browsertrix'),
        default='text',
        help='Format of seeds output.'
    )
    multi_seeds_command.add_argument(
        '--pattern',
        help='Only list URLs matching this pattern.'
    )
    multi_seeds_command.add_argument(
        '--workers',
        type=int,
        default=2,
        help='How many workers (browserstrix only).'
    )
    multi_seeds_command.add_argument(
        '--size',
        type=int,
        default=1000,
        help='How many URLs per seed list.'
    )
    multi_seeds_command.add_argument(
        '--output',
        type=Path,
        default=Path('.'),
        help='Directory to write seed lists to.'
    )
    multi_seeds_command.set_defaults(func=generate_multi_seeds)

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


def generate_multi_seeds(*, pattern, workers: int, output: Path, size: int, **_kwargs) -> None:
    print(f'Writing seed files to "{output}/*"...', file=stderr)
    output.mkdir(parents=True, exist_ok=True)
    filename_template = '{name}.seeds.yaml'

    files = []

    urls = active_urls(pattern=pattern)
    core_groups = group_urls(urls, by='domain')

    oversized = [k for k, v in core_groups.items() if len(v) >= size]
    for group in oversized:
        urls = core_groups.pop(group)
        for index, subset in enumerate(batched(urls, size)):
            file_group = group.replace('.', '-')
            filename = filename_template.format(name=f'{file_group}-{index + 1}')
            with open(output / filename, 'w') as file:
                file.write(format_browsertrix(subset, workers=1))
                files.append(filename)
                print(f'Wrote "{file.name}"', file=stderr)

    subsets = []
    while len(core_groups):
        subset = []
        remaining = size
        for group, urls in core_groups.copy().items():
            if len(urls) <= remaining:
                core_groups.pop(group)
                subset.extend(urls)
                remaining -= len(urls)
                if remaining == 0:
                    break

        subsets.append(subset)

    for index, subset in enumerate(subsets):
        filename = filename_template.format(name=f'other-{index + 1}')
        with open(output / filename, 'w') as file:
            file.write(format_browsertrix(subset, workers=workers))
            files.append(filename)
            print(f'Wrote "{file.name}"', file=stderr)

    print(json.dumps([f.split('.seeds')[0] for f in files]))

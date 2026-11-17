"""Windows CMD: python konvi.py "vhod.xml" ["izhod.xml"]."""
import argparse
from pathlib import Path
import sys

from converter import ConversionError, convert_file


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Pretvori REK-1b v REK-O brez seštevanja zneskov.',
        usage='python konvi.py vhod.xml [izhod.xml]',
    )
    parser.add_argument('vhod', type=Path, help='Vhodna datoteka REK-1b XML')
    parser.add_argument('izhod', nargs='?', type=Path,
                        help='Izhodna datoteka; privzeto vhod_REK_O.xml')
    args = parser.parse_args(argv)
    source = args.vhod
    destination = args.izhod or source.with_name(source.stem + '_REK_O.xml')
    try:
        if source.resolve() == destination.resolve():
            raise ConversionError('Vhodna in izhodna datoteka morata biti različni.')
        if destination.exists():
            raise ConversionError(f'Izhodna datoteka že obstaja: {destination}. Izberi drugo ime.')
        result, count = convert_file(source)
        # Exclusive creation also prevents overwriting an existing file in a race.
        with destination.open('xb') as stream:
            try:
                stream.write(result)
            except OSError:
                stream.close()
                destination.unlink(missing_ok=True)
                raise
    except (ConversionError, OSError) as exc:
        print(f'Napaka: {exc}', file=sys.stderr)
        return 1
    print(f'Pretvorjeno: {source} -> {destination}')
    print(f'Število postavk: {count}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

import random
import string

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from csv_export.models import Example, LightweightExample


DEFAULT_COUNT = 2_000_000
DEFAULT_SEED = 42
LIGHTWEIGHT_COUNT = 10
VALUE_LENGTH = 16
ALPHABET = string.ascii_lowercase + string.digits


class Command(BaseCommand):
    help = (
        'Replaces the Example tables with reproducible pseudorandom data. '
        'By default it creates 2,000,000 Example rows and 10 lightweight rows '
        'using seed 42.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=DEFAULT_COUNT)
        parser.add_argument('--seed', type=int, default=DEFAULT_SEED)

    def handle(self, *args, **options):
        count = options['count']
        seed = options['seed']

        if count < 0:
            raise CommandError('--count cannot be negative.')
        if connection.vendor != 'postgresql':
            raise CommandError('This command requires PostgreSQL because it uses COPY.')

        rng = random.Random(seed)
        table = connection.ops.quote_name(Example._meta.db_table)
        columns = ('col_a', 'col_b', 'col_c', 'col_d')

        self.stdout.write(
            f'Generating {count:,} reproducible rows with seed {seed}...'
        )

        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(f'TRUNCATE TABLE {table} RESTART IDENTITY')

            copy_sql = (
                f'COPY {table} ({", ".join(columns)}) '
                'FROM STDIN WITH (FORMAT TEXT)'
            )
            with cursor.copy(copy_sql) as copy:
                for _ in range(count):
                    copy.write_row(
                        tuple(self._random_value(rng) for _ in columns)
                    )

            lightweight_rng = random.Random(seed + 1)
            LightweightExample.objects.all().delete()
            LightweightExample.objects.bulk_create([
                LightweightExample(
                    name=f'item-{index + 1:02d}',
                    value=lightweight_rng.randint(1, 1_000),
                )
                for index in range(LIGHTWEIGHT_COUNT)
            ])

        self.stdout.write(
            self.style.SUCCESS(
                f'Tables loaded successfully with {count:,} Example rows and '
                f'{LIGHTWEIGHT_COUNT} lightweight rows.'
            )
        )

    @staticmethod
    def _random_value(rng):
        return ''.join(rng.choices(ALPHABET, k=VALUE_LENGTH))

import argparse
import os
import sys
import time
import tracemalloc
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from rest_framework.test import APIRequestFactory

from csv_export.views import export_examples_v1, export_examples_v2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('version', choices=('v1', 'v2'))
    parser.add_argument('output')
    args = parser.parse_args()

    request = APIRequestFactory().get(
        f'/csv/examples/export/{args.version}/',
        {'filename': os.path.basename(args.output)},
    )
    view = export_examples_v1 if args.version == 'v1' else export_examples_v2
    tracemalloc.start()
    started = time.perf_counter()
    response = view(request)

    with open(args.output, 'wb') as output:
        if response.streaming:
            for chunk in response.streaming_content:
                output.write(chunk)
        else:
            output.write(response.content)
    response.close()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f'status={response.status_code}', flush=True)
    print(f'bytes={os.path.getsize(args.output)}', flush=True)
    print(f'peak_mb={peak / 1024 / 1024:.2f}', flush=True)
    print(f'elapsed_seconds={time.perf_counter() - started:.2f}', flush=True)


if __name__ == '__main__':
    main()

from django.core.management.base import BaseCommand, CommandError
from image_lite.management.commands import common
from pathlib import Path



class Command(BaseCommand):
    help = 'Automatically/bulk delete reform images'
    output_transaction = True

    def add_arguments(self, parser):
        common.add_model_argument(parser)
        common.add_contains_argument(parser)
        
    def handle(self, *args, **options):
        reform_path = common.get_reform_path(options)
        reform_list = [fp for fp in reform_path.iterdir() if fp.is_file()]
        contains_test = options["contains"]
        if (contains_test):
            reform_list = filter(lambda fn: contains_test in str(fn), reform_list)
        count = 0
        for fp in reform_list:
            try:
                Path(fp).unlink(missing_ok=False)
                count += 1
            except FileNotFoundError:
                # ignore, and carry on
                pass
        if (options['verbosity'] > 0):
            print("{} reforms deleted".format(count)) 

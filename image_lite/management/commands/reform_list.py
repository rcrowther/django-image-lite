import datetime

from django.core.management.base import BaseCommand, CommandError
from image_lite.management.commands import common
from pathlib import Path



class Command(BaseCommand):
    help = 'List reforms.'
    
    def add_arguments(self, parser):
        common.add_model_argument(parser)
        common.add_contains_argument(parser)
                
    def handle(self, *args, **options):
        reform_path = common.get_reform_path(options)
        reform_list = [fp.stem for fp in reform_path.iterdir() if fp.is_file()]
        contains_test = options["contains"]
        if (contains_test):
            reform_list = filter(lambda fn: contains_test in fn, reform_list)
        rl = sorted(reform_list)
        for fp in rl:
            print(fp)

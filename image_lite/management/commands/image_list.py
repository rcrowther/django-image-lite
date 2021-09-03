import datetime

from django.core.management.base import BaseCommand, CommandError
from image_lite.management.commands import common
from pathlib import Path



class Command(BaseCommand):
    help = 'List images'
    output_transaction = True
    
    def add_arguments(self, parser):
        common.add_model_argument(parser)
        common.add_contains_argument(parser)
        parser.add_argument(
            '-w',
            '--weeks-back',
            type=int,
            help='Search for entries from now to "count" weeks back',
        )
                
    def handle(self, *args, **options):
        Model = common.get_image_model(options)
        qs = Model.objects
        qs = common.filter_query_contains(options, qs)
        if (options["weeks_back"]):
            week_num_now =  datetime.date.isocalendar(datetime.date.today())[1]
            
            if (options["weeks_back"] > week_num_now or options["weeks_back"] < 0):
                raise CommandError("Value of --weeks_back option cant be negative or larger than the year. Today is in week {}".format(week_num_now))             
            week_num_back = week_num_now - options["weeks_back"]
            qs = qs.filter(upload_date__week__gte=week_num_back)

        for e in qs.all():
            print("{} {}".format(e.pk, Path(e.src.name).stem))

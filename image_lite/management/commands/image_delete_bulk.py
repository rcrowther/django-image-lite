from django.core.management.base import BaseCommand, CommandError
from image_lite.management.commands import common



class Command(BaseCommand):
    help = 'Automatically/bulk delete images'
    output_transaction = True

    def add_arguments(self, parser):
        common.add_model_argument(parser)
        common.add_contains_argument(parser)
        parser.add_argument(
            '--bulk',
            action='store_true',
            help='Delete images by SQL (fast, but less robust)',
        )

    def handle(self, *args, **options):
        Model = common.get_image_model(options)
        qs = Model.objects.all()
        qs = common.filter_query_contains(options, qs)
        
        if options['bulk']:
            r = qs.delete()            
            if (options['verbosity'] > 0):
                print("{} image(s) deleted".format(r[0])) 
        else:
            count = 0
            for im in qs:
                r = im.delete()
                
                # count from return. May have failed!
                count += r[0]

            if (options['verbosity'] > 0):
                print("{} image(s) deleted".format(count)) 

from pathlib import Path
import os
from django.core.management.base import BaseCommand, CommandError
from django.core.files.images import ImageFile
from image_lite.management.commands import common



class Command(BaseCommand):
    help = 'Automatically/bulk add images to an image model. The command tries to ignore errors and continue. It will append to existing collections. Attributes other than file data will default.'

    def add_arguments(self, parser):
        common.add_model_argument(parser)
        parser.add_argument(
            'src_path', 
            type=str
        )

                         
    def handle(self, *args, **options):
        Model = common.get_image_model(options)
            
        # get the path of src dir
        src_path = options['src_path']
        src_dir = Path(src_path)
        if (not(src_dir.is_dir())):
            raise CommandError("Source provided is not recognised as a directory. path: '{}'".format(src_path))
        
        # get full paths of files in the src dir
        src_filepaths = [f.resolve() for f in src_dir.iterdir() if f.is_file()]
       
        # build models and save
        # I think we can not use bulk_create because we want to be 
        # cautious and succeed as much as possible
        count = 0
        fail = []
        for path in src_filepaths:
            with open(path, 'rb') as f:                
                basename = os.path.basename(path)
                #media_relative_path = os.path.join(root, basename) 
                i = Model(
                    src = ImageFile(f, name=basename),
                ) 
                try:
                    i.save()
                    count += 1
                except Exception:
                    fail.append(basename)
        
        # output some results            
        if (options['verbosity'] > 0):
            print("{} image(s) created".format(count)) 
            if (len(fail) > 0):
                print("{} image(s) failed save. Basenames: '{}'".format(
                    len(fail),
                    "', '".join(fail),
                    )) 

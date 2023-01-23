from pathlib import Path
import os
from django.core.management.base import BaseCommand, CommandError
from django.core.files.images import ImageFile
from image_lite.management.commands import common
from image_lite import registry



class Command(BaseCommand):
    help = 'Automatically/bulk generate reforms to an image model. The command tries to ignore errors and continue. It will append to existing collections. Attributes other than file data will default.'

    def add_arguments(self, parser):
        common.add_model_argument(parser)
        # parser.add_argument(
            # 'src_path', 
            # type=str
        # )


    #! accept liat of filter names
    def handle(self, *args, **options):
        Model = common.get_image_model(options)
        
        #- get storage
        storage = common.get_storage(Model)
        
        # Get full reform path
        reform_path_from_media = common.get_reform_path(options)
        reform_base_path = Path(storage.location) / reform_path_from_media

        # Need to...
        #- get filters, 
        filters = Model.get_filters()

        # get filenames DB holds
        images_qs = Model.objects.all() #values_list('src', flat=True)

        count = 0
        ignored = 0
        fail = []
        for image in images_qs:
            # construct a basic reform path
            src_filename = Path(image.src.name).stem

            # first write will be to the reform_base_path
            # (subsequent to subdirectories)
            reform_file_subpath = reform_base_path
        
            # We've only got started....
            first = True
            for filter_class in filters:
                if (not(first)):
                    reform_file_subpath = Path(reform_base_path) / filter_class.classname_as_path_segment()
                first = False

                #  make up full filepath
                reform_path = Path(reform_file_subpath) / (src_filename + '.' + filter_class.format)
              
                # - bail if file exists 
                if (reform_path.exists()):
                    ignored += 1
                    continue
         
                # - run filter on existing files
                with image.src.open() as fsrc:
                    filter_instance = filter_class()
                    (reform_buff, iformat) = filter_instance.process(
                        fsrc,
                        #model_args
                        {}
                    )

                # save
                with open(reform_path, "wb") as f:
                    try:
                        f.write(reform_buff.getbuffer()) 
                        count += 1
                    except Exception:
                        fail.append(reform_path)
                    
        # output some results            
        if (options['verbosity'] > 0):
            print(f"{count} image(s) created") 
            print(f"{ignored} reform images ignored because they exist")
            if (len(fail) > 0):
                print("{} image(s) failed save. Basenames: '{}'".format(
                    len(fail),
                    "', '".join(fail),
                    )) 


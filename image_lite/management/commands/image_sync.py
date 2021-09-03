from django.core.management.base import BaseCommand
from pathlib import Path
from image_lite.management.commands import common



class Command(BaseCommand):
    help = 'Resync local image files to the database. Default is to print status.'
    output_transaction = True
    
    def add_arguments(self, parser):
        common.add_model_argument(parser)
        parser.add_argument(
            '--remove-orphaned-files',
            action='store_true',
            help='Delete orphaned files',
        )
        parser.add_argument(
            '-a',
            '--add-orphaned-files',
            action='store_true',
            help='Add models for orphaned files (model attributes default)',
        )
        parser.add_argument(
            '--remove-orphaned-models',
            action='store_true',
            help='Delete orphaned models (with no matching file)',
        )        
        
    def originals_fp_list(self, file_dir):
        return [f for f in file_dir.iterdir() if f.is_file()]

    def db_image_fp_list(self, Model, storage_location):
        ''' 
        Read all image model paths
        return 
            full-path Paths
        '''
        val_list = Model.objects.values_list('src', flat=True)
        return [storage_location / rel_path for rel_path in val_list]
            
    def db_image_list(self, Model, storage_location):
        ''' 
        Read all image models for pk and src
        return
            list -> dict {fieldname: fieldvalue} supplemented with 'full_path' key/value
        '''
        val_list = Model.objects.values('pk', 'src')
        for e in val_list:
            e['full_path']  = storage_location / e['src']
        return  val_list  

    def db_image_count(self, Model):
        return Model.objects.count()
        
    def handle(self, *args, **options):        
        Model = common.get_image_model(options)
        
        # get the model dir path
        # Mad Django
        storage = Model._meta.get_field('src').storage 
          
        # location is MEDIA_ROOT for local files
        location = Path(storage.location)
        
        # path is a path constructor from MEDIA_ROOT
        file_dir = Path(storage.path(Model.upload_dir))    
        fl = self.originals_fp_list(file_dir)
        
        if options['remove_orphaned_models']:            
            dbl = self.db_image_list(Model, location)
            model_no_file = [m for m in dbl if not(m['full_path'] in fl)]           
            pks = [m['pk'] for m in model_no_file]
            r = Model.objects.filter(pk__in=pks).delete()
            if (options['verbosity'] > 0):
                print("{} model(s) deleted".format(r[0])) 
            if (options['verbosity'] > 2):
                for m in model_no_file:
                    print(m['src'])
                    
        elif options['remove_orphaned_files']:
            count = 0
            fail = []
            dbl = self.db_image_fp_list(Model, location)
            file_no_model = set(fl) - set(dbl)
            for path in file_no_model:
                try:
                    path.unlink()
                    count += 1
                except Exception:
                    fail.append(path.stem)
            if (options['verbosity'] > 0):
                print("{} image(s) deleted".format(count)) 
                if (len(fail) > 0):
                    print("{} image(s) failed to delete. Path: '{}'".format(
                        len(fail),
                        "', '".join(fail),
                        ))
        elif options['add_orphaned_files']:
            # Add models for orphaned files
            count = 0
            fail = []
            dbl = self.db_image_fp_list(Model, location)
            file_no_model = set(fl) - set(dbl)
            for path in file_no_model:
                # Make new models.
                # Worth explaining:
                # How do we register orphaned files?
                # When the model is saved, the generated FieldFile will 
                # not recognise the file is stored and attempt a copy 
                # onto itself. This should fail silently, in linux, 
                # but Django throws a FileExistsError, then makes a 
                # renamed copy.
                # Preferebly, we would tell FieldFile the storage is 
                # committed. Interesingly, a simple string path, as 
                # opposed to an open File or Imagefile, assumes the
                # image is commited.
                #
                # The update effect in Imagefields will not work with 
                # Paths, only strings. Also, it works relative to /media
                # (so path relativization here)
                #
                # Presuming all is default in the new model. If you need
                # to use this command, sure you can work from there.
                i = Model(
                    src = str(Path(Model.upload_dir) / path.name),
                ) 
                try:
                    i.save()
                    count += 1
                except Exception:
                    fail.append(path.stem)
        
            if (options['verbosity'] > 0):
                print("{} image(s) created".format(count)) 
                if (len(fail) > 0):
                    print("{} image(s) failed import. Path: '{}'".format(
                        len(fail),
                        "', '".join(fail),
                        )) 
        else:
            # status report
            if (options['verbosity'] > 0):
                header = "SYNC STATUS: {}".format(Model.__name__)
                print("-" * (len(header) + 1))
                print(header)
                print("-" * (len(header) + 1))
            model_count = self.db_image_count(Model)
            file_count = len(fl)
            if ( (model_count != file_count) or options['verbosity'] > 0):
                print("model_count: {}".format(model_count))
                print("file_count: {}".format(file_count))
            if (model_count > file_count):
                print('[warning] files appear to be missing. Try --remove-orphaned-models')
            elif (file_count > model_count):
                print('[warning] models appear to be missing. Try --add-orphaned-files or --remove-orphaned-files')
            else:
                print('** No sync issues detected')
            
            

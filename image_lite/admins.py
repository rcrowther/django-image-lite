import copy
from django.contrib import admin
from django.utils.html import format_html



class ImageLiteAdmin(admin.ModelAdmin):
    '''
    Admin devised for maintenence of ImageLite models.
    Ot's more informative than stock.
    '''
    #! All the below can be commented or adapted to remove/change 
    # particular effects.
    # See the notes.
    #
    # case-insensitive 'contains' match
    search_fields = ['src']
    
    # Style the lists.
    # See the support code below
    list_display = ('filename', 'upload_day', 'image_delete', 'image_view',)
        
    # Support code for styling the admin list
    # See the 'list_display' attribute.
    def image_view(self, obj):
        return format_html('<a href="{}" class="button">View</a>',
            obj.src.url
        )
    image_view.short_description = 'View'

    def image_delete(self, obj):
        return format_html('<a href="{}/delete" class="button" style="background: #ba2121;color: #fff;">Delete</a>',
            obj.pk
        )
    image_delete.short_description = 'Delete'
    
    def upload_day(self, obj):
        '''e.g.	17 May 2020'''
        return format_html('{}',
            obj.upload_time.strftime("%d %b %Y")
        )
    upload_day.short_description = 'Upload day'
    upload_day.admin_order_field = '_upload_time'

    def filename(self, obj):
        return obj.filename
    filename.admin_order_field = 'src'
    
    # if you want to change the filechooser on the add form, you
    # can do it here. The default is
    # admin.widgets.AdminFileWidget
    #formfield_overrides = {
        ## For example, Drag and drop Image picker from,
        ## https://github.com/rcrowther/DDFileChooser
        #ImageFileField: {'widget': DDFileChooser},
    #}        

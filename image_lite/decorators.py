def register():
    """
    Register the given filter classes with the image app:

    @register()
    class Thumb(filters_pillow.ResizeSmart):
        width=64
        height=64
    """
    from image_lite import Filter, registry

    def _filter_wrapper(filter_class):

        if not issubclass(filter_class, Filter):
            raise ValueError('Wrapped class must subclass image.Filter.')
            
        registry.register(filter_class)

        return filter_class

    return _filter_wrapper

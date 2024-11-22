def with_savepoint(exception=Exception):
    def _with_savepoint(f):
        def wrapper(self, *args, **kwargs):
            with self.env.cr.savepoint():
                try:
                    return f(self, *args, **kwargs)
                except Exception as e:
                    raise exception(str(e))
        return wrapper
    return _with_savepoint

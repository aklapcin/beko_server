from werkzeug.routing import BaseConverter

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

def get_or_404(model, ident):
    rv = model.query.get(ident)
    if rv is None:
        abort(404)
    return rv
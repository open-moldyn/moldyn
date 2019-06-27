def _float(w, default=None):
    if default==None:
        return float(w.text().replace(",", "."))
    else:
        try:
            return _float(w)
        except:
            w.setText(str(default))
            return default

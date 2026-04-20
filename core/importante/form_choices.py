def choices_presentes(desde_bd, choices_base):
    """Filtra choices_base dejando solo códigos presentes en BD.

    - Conserva el orden y etiqueta de choices_base.
    - Si en BD aparecen códigos no contemplados en choices_base, los agrega al final.
    """

    presentes = set(desde_bd)
    if not presentes:
        return []

    base_codigos = [codigo for codigo, _ in choices_base]
    choices = [(codigo, etiqueta) for codigo, etiqueta in choices_base if codigo in presentes]

    extras = sorted(presentes.difference(base_codigos))
    choices.extend([(codigo, str(codigo)) for codigo in extras])
    return choices

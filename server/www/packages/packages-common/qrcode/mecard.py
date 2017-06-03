import six

# {'code': 'N', 'label': 'Name', 'required': True, 'multipart': [
#     'Last Name', 'First Name']},
PROPERTIES = {
    'NICKNAME': {'label': 'Nickname'},
    'BDAY': {'label': 'Birthday', 'date': True},
    'TEL': {'label': 'Phone'},
    'EMAIL': {'label': 'E-mail'},
    'ADR': {'label': 'Address', 'multipart': [
        'PO Box', 'Room Number', 'House Number', 'City', 'Prefecture',
        'Zip Code', 'Country']},
    'URL': {'label': 'URL'},
    'MEMO': {'label': 'Note'},
}


def build_code(data):
    notation = []

    name = data['N']
    if not isinstance(name, six.text_type):
        name = ','.join(name)
    notation.append('N', name)

    for prop in PROPERTIES:
        value = data.get(prop['code'])
        if not value:
            continue
        if prop['date']:
            value = value.strftime('%Y%m%d')
        elif prop['multipart']:
            value = ','.join(value)

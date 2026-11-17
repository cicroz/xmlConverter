"""Pretvorba REK-1b v REK-O z neposrednim prenosom zneskov iz starega obrazca."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from pathlib import Path
from lxml import etree

NS_REKO = 'http://edavki.durs.si/Documents/Schemas/REK_O_1.xsd'
NS_EDP = 'http://edavki.durs.si/Documents/Schemas/EDP-Common-1.xsd'
NS_ANALYTICAL = 'http://edavki.durs.si/Documents/Schemas/REK_O_Analytical_1.xsd'
NS = {'rek': 'http://edavki.durs.si/Documents/Schemas/REK_1b_2.xsd',
      'edp': NS_EDP, 'podo': 'http://edavki.durs.si/Documents/Schemas/PODO-Common-1.xsd'}

class ConversionError(ValueError):
    """Vhodnih podatkov ni mogoče pretvoriti."""

def _required(parent, path):
    value = parent.findtext(path, namespaces=NS)
    if not value or not value.strip():
        raise ConversionError(f'Manjka obvezni podatek: {path.split(":")[-1]}.')
    return value.strip()

def convert_file(source: str | Path) -> tuple[bytes, int]:
    parser = etree.XMLParser(remove_blank_text=True, resolve_entities=False, no_network=True, load_dtd=False)
    try:
        tree = etree.parse(str(source), parser)
    except (etree.XMLSyntaxError, OSError) as exc:
        raise ConversionError(f'Datoteke XML ni mogoče prebrati: {exc}') from exc
    if tree.docinfo.doctype:
        raise ConversionError('Dokumenti z deklaracijo DTD niso podprti.')
    root = tree.getroot()
    taxpayer = root.find('edp:Header/edp:taxpayer', NS)
    rek = root.find('.//rek:REK_1b', NS)
    if taxpayer is None or rek is None:
        raise ConversionError('Pričakovan je REK-1b XML z glavo edp:Header/edp:taxpayer in elementom REK_1b.')
    out = etree.Element(etree.QName(NS_REKO, 'Envelope'), nsmap={None: NS_REKO, 'edp': NS_EDP})
    def add(parent, tag, value=None, ns=NS_REKO):
        child = etree.SubElement(parent, etree.QName(ns, tag))
        child.text = value
        return child
    add(out, 'Header', ns=NS_EDP).append(deepcopy(taxpayer))
    add(out, 'Signatures', ns=NS_EDP)
    body = add(out, 'body')
    add(body, 'bodyContent', ns=NS_EDP)
    rek_out = add(body, 'REK')
    header = add(rek_out, 'REK_O')
    for key, value in [('DocumentType', 'O'), ('F004', 'false'),
                       ('F008', _required(rek, 'rek:F008_ResponsiblePerson')),
                       ('F009', _required(rek, 'rek:F009_PhoneNumber').replace(' ', '')),
                       ('F010', '1096'), ('F010a', 'false'),
                       ('F011Start', _required(rek, 'rek:F11_MonthYearStart')),
                       ('F012', _required(rek, 'rek:F12_PaymentDate'))]:
        add(header, key, value)
    analytical = etree.SubElement(rek_out, etree.QName(NS_ANALYTICAL, 'AnalyticalData'), nsmap={None: NS_ANALYTICAL, 'edp': NS_EDP})
    items = root.findall('.//podo:AnalyticalDataItem', NS)
    if not items:
        raise ConversionError('Datoteka ne vsebuje postavk AnalyticalDataItem.')
    def copy_amount(parent, source_tag, target, destination, namespace, label):
        element = parent.find(source_tag, NS)
        if element is None:
            return
        value = (element.text or '').strip()
        try:
            amount = Decimal(value)
            if not amount.is_finite() or abs(amount) >= Decimal('1e30'):
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            raise ConversionError(f'{label}: {source_tag} vsebuje neveljaven znesek ({value}).') from None
        # Preserve the supplied value; do not round, sum or invent defaults.
        add(target, destination, value, ns=namespace)

    for index, item in enumerate(items, 1):
        target = add(analytical, 'AnalyticalDataItem', ns=NS_ANALYTICAL)
        for dest, source_tag in [('A001', 'A001'), ('A003', 'A003i'), ('A003a', 'A003p'), ('A004', 'A004')]:
            add(target, dest, _required(item, f'podo:{source_tag}'), ns=NS_ANALYTICAL)
        for number in range(81, 87):
            for suffix in ('O', 'P'):
                field = f'A{number:03d}{suffix}'
                copy_amount(item, f'podo:{field}', target, field, NS_ANALYTICAL, f'Postavka {index}')

    # Old REK-1b F401..F405 -> REK-O F301..F305. Old Z means
    # "za plačilo"; do not derive it from O or the analytical items.
    for old_number, new_number in zip(range(401, 406), range(301, 306)):
        account = rek.find(f'rek:F{old_number}R', NS)
        if account is not None:
            add(header, f'F{new_number}R', account.text)
        for old_suffix, new_suffix in [('O', 'O'), ('Z', 'P')]:
            copy_amount(rek, f'rek:F{old_number}{old_suffix}', header,
                        f'F{new_number}{new_suffix}', NS_REKO, 'Zbirni del')
    return etree.tostring(out, pretty_print=True, xml_declaration=True, encoding='UTF-8'), len(items)

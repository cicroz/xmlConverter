import tempfile
import unittest
from pathlib import Path
from lxml import etree
from converter import convert_file, ConversionError, NS, NS_REKO, NS_ANALYTICAL

XML = f'''<Envelope xmlns="{NS['rek']}" xmlns:edp="{NS['edp']}" xmlns:p="{NS['podo']}">
<edp:Header><edp:taxpayer><edp:taxNumber>12345678</edp:taxNumber></edp:taxpayer></edp:Header>
<body><REK_1b><F008_ResponsiblePerson>Test</F008_ResponsiblePerson><F009_PhoneNumber>01 123 456</F009_PhoneNumber><F11_MonthYearStart>2026-10</F11_MonthYearStart><F12_PaymentDate>2026-11-17</F12_PaymentDate><F401O>18.00</F401O><F401Z>0.00</F401Z><F401R>original account</F401R><F402O>7.72</F402O></REK_1b>
<p:AnalyticalDataItem><p:A001>1</p:A001><p:A003i>Ime</p:A003i><p:A003p>Priimek</p:A003p><p:A004>SI</p:A004><p:A081SZ>4.87</p:A081SZ><p:A081SF>true</p:A081SF><p:A082SZ>7.72</p:A082SZ><p:A082SF>true</p:A082SF><p:A082O>7.72</p:A082O><p:A086O>7.72</p:A086O></p:AnalyticalDataItem>
</body></Envelope>'''

class ConversionTests(unittest.TestCase):
    def convert(self, data=XML):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.xml'
            path.write_text(data, encoding='utf-8')
            before = path.read_bytes()
            result = convert_file(path)
            self.assertEqual(path.read_bytes(), before)
            return result

    def test_mapping_and_totals(self):
        data, count = self.convert()
        root = etree.fromstring(data)
        ns = {'r': NS_REKO, 'a': NS_ANALYTICAL, 'edp': NS['edp']}
        self.assertEqual(count, 1)
        for tag, value in [('F009', '01123456'), ('F301O', '18.00'), ('F301P', '0.00'), ('F301R', 'original account'), ('F302O', '7.72'), ('F010', '1096')]:
            self.assertEqual(root.findtext('.//r:' + tag, namespaces=ns), value)
        self.assertEqual(root.findtext('.//a:A086O', namespaces=ns), '7.72')
        self.assertEqual(root.findtext('.//a:A003', namespaces=ns), 'Ime')
        self.assertEqual(root.findtext('edp:Header/edp:taxpayer/edp:taxNumber', namespaces=ns), '12345678')
        self.assertEqual(root.tag, f'{{{NS_REKO}}}Envelope')

    def test_multiple_items(self):
        root = etree.fromstring(XML.encode())
        item = root.find('.//p:AnalyticalDataItem', {'p': NS['podo']})
        from copy import deepcopy
        item.getparent().append(deepcopy(item))
        data, count = self.convert(etree.tostring(root).decode())
        self.assertEqual(count, 2)
        self.assertEqual(etree.fromstring(data).findtext(f'.//{{{NS_REKO}}}F301O'), '18.00')

    def test_missing_amounts_are_not_created(self):
        data, _ = self.convert()
        root = etree.fromstring(data)
        for field in ('A081O', 'A081P', 'A082P', 'A086P'):
            self.assertIsNone(root.find(f'.//{{{NS_ANALYTICAL}}}{field}'))
        self.assertIsNone(root.find(f'.//{{{NS_REKO}}}F302P'))
        self.assertIsNone(root.find(f'.//{{{NS_REKO}}}F302R'))

    def test_distinct_amounts_and_totals_are_preserved(self):
        extra = '<p:A081O>1.20</p:A081O><p:A081P>0.00</p:A081P><p:A086P>0.50</p:A086P><p:A083O>3.10</p:A083O>'
        data, _ = self.convert(XML.replace('</p:AnalyticalDataItem>', extra + '</p:AnalyticalDataItem>'))
        root = etree.fromstring(data)
        for field, value in [('A081O', '1.20'), ('A081P', '0.00'), ('A086O', '7.72'), ('A086P', '0.50'), ('A083O', '3.10')]:
            self.assertEqual(root.findtext(f'.//{{{NS_ANALYTICAL}}}{field}'), value)

    def test_missing_totals_are_not_calculated(self):
        data, _ = self.convert(XML.replace('<p:A086O>7.72</p:A086O>', ''))
        self.assertIsNone(etree.fromstring(data).find(f'.//{{{NS_ANALYTICAL}}}A086O'))

    def test_invalid_inputs(self):
        for data in ['<bad', '<other/>', XML.replace('<p:A082O>7.72', '<p:A082O>NaN'), XML.replace('<F401O>18.00', '<F401O>abc'), XML.replace('<p:A086O>7.72', '<p:A086O>'), XML.replace('<F009_PhoneNumber>01 123 456</F009_PhoneNumber>', ''), '<!DOCTYPE Envelope>' + XML]:
            with self.subTest(data=data[:50]), self.assertRaises(ConversionError):
                self.convert(data)

    def test_no_items(self):
        root = etree.fromstring(XML.encode())
        item = root.find('.//p:AnalyticalDataItem', {'p': NS['podo']})
        item.getparent().remove(item)
        with self.assertRaises(ConversionError):
            self.convert(etree.tostring(root).decode())

if __name__ == '__main__':
    unittest.main()

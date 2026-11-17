from lxml import etree
from lxml.etree import QName
from decimal import Decimal

# === Imena datotek ===
rek1b_file = "reki (3).xml"
rek_o_file = "converted RekO.xml"

# === Namespace-i ===
NS_REKO = "http://edavki.durs.si/Documents/Schemas/REK_O_1.xsd"
NS_EDP = "http://edavki.durs.si/Documents/Schemas/EDP-Common-1.xsd"
NS_ANALYTICAL = "http://edavki.durs.si/Documents/Schemas/REK_O_Analytical_1.xsd"
NS_REK1B = {
    "rek": "http://edavki.durs.si/Documents/Schemas/REK_1b_2.xsd",
    "edp": NS_EDP,
    "podo": "http://edavki.durs.si/Documents/Schemas/PODO-Common-1.xsd"
}

def analytical_tag(tag):
    return QName(NS_ANALYTICAL, tag)

# === Branje vhodne XML ===
parser = etree.XMLParser(remove_blank_text=True)
tree = etree.parse(rek1b_file, parser)
root = tree.getroot()

# === Osnovna struktura REK_O ===
reko_root = etree.Element("Envelope", nsmap={
    None: NS_REKO,
    "edp": NS_EDP
})

header = root.find("edp:Header", namespaces=NS_REK1B)
reko_header = etree.SubElement(reko_root, QName(NS_EDP, "Header"))
reko_header.append(header.find("edp:taxpayer", namespaces=NS_REK1B))

etree.SubElement(reko_root, QName(NS_EDP, "Signatures"))
body = etree.SubElement(reko_root, "body")
etree.SubElement(body, QName(NS_EDP, "bodyContent"))

rek_elem = etree.SubElement(body, "REK")
rek_o = etree.SubElement(rek_elem, "REK_O")

rek1b = root.find(".//rek:REK_1b", namespaces=NS_REK1B)

# === Glava REK_O ===
etree.SubElement(rek_o, "DocumentType").text = "O"
etree.SubElement(rek_o, "F004").text = "false"
etree.SubElement(rek_o, "F008").text = rek1b.findtext("rek:F008_ResponsiblePerson", namespaces=NS_REK1B)
etree.SubElement(rek_o, "F009").text = rek1b.findtext("rek:F009_PhoneNumber", namespaces=NS_REK1B).replace(" ", "")
etree.SubElement(rek_o, "F010").text = "1096"
etree.SubElement(rek_o, "F010a").text = "false"
etree.SubElement(rek_o, "F011Start").text = rek1b.findtext("rek:F11_MonthYearStart", namespaces=NS_REK1B)
etree.SubElement(rek_o, "F012").text = rek1b.findtext("rek:F12_PaymentDate", namespaces=NS_REK1B)

# === AnalyticalData ===
analytical = etree.Element(
    QName(NS_ANALYTICAL, "AnalyticalData"),
    nsmap={
        None: NS_ANALYTICAL,
        "edp": NS_EDP
    }
)
rek_elem.append(analytical)

sum_f401z = Decimal("0.00")
sum_f402z = Decimal("0.00")

# === Zanka čez zavezance ===
for item in root.findall(".//podo:AnalyticalDataItem", namespaces=NS_REK1B):
    new_item = etree.SubElement(analytical, analytical_tag("AnalyticalDataItem"))
    etree.SubElement(new_item, analytical_tag("A001")).text = item.findtext("podo:A001", namespaces=NS_REK1B)
    etree.SubElement(new_item, analytical_tag("A003")).text = item.findtext("podo:A003i", namespaces=NS_REK1B)
    etree.SubElement(new_item, analytical_tag("A003a")).text = item.findtext("podo:A003p", namespaces=NS_REK1B)
    etree.SubElement(new_item, analytical_tag("A004")).text = item.findtext("podo:A004", namespaces=NS_REK1B)

    # Branje in pretvorba v decimal
    a081 = Decimal(item.findtext("podo:A081SZ", "0", namespaces=NS_REK1B))
    a082 = Decimal(item.findtext("podo:A082SZ", "0", namespaces=NS_REK1B))
    a086 = a081 + a082

    etree.SubElement(new_item, analytical_tag("A081O")).text = f"{a081:.2f}"
    etree.SubElement(new_item, analytical_tag("A081P")).text = f"{a081:.2f}"
    etree.SubElement(new_item, analytical_tag("A082O")).text = f"{a082:.2f}"
    etree.SubElement(new_item, analytical_tag("A082P")).text = f"{a082:.2f}"
    etree.SubElement(new_item, analytical_tag("A086O")).text = f"{a086:.2f}"
    etree.SubElement(new_item, analytical_tag("A086P")).text = f"{a086:.2f}"

    # Za glavo REK_O
    sum_f401z += a081
    sum_f402z += a082

# === Zneski na račune ===
etree.SubElement(rek_o, "F301R").text = "SI5601100-8882000003 SI19 79826989-44008"
etree.SubElement(rek_o, "F301O").text = f"{sum_f401z:.2f}"
etree.SubElement(rek_o, "F301P").text = f"{sum_f401z:.2f}"
etree.SubElement(rek_o, "F302R").text = "SI5601100-8883000073 SI19 79826989-45004"
etree.SubElement(rek_o, "F302O").text = f"{sum_f402z:.2f}"
etree.SubElement(rek_o, "F302P").text = f"{sum_f402z:.2f}"

# === Shrani v XML datoteko ===
etree.ElementTree(reko_root).write(rek_o_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
print(f"✅ Pretvorjeno: '{rek1b_file}' → '{rek_o_file}'")

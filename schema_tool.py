import xml.etree.ElementTree as ET
import re
import sys
import os
pattern = r'("[^"]*")'


def isEnum(vtype):
    if vtype.find("::Enum") != -1:
        return True
    return False


def isVector(vtype):
    if vtype.find("std::vector") != -1:
        return True
    return False


def isMap(vtype):
    if vtype.find("std::map") != -1:
        return True
    return False


def c_process_vector(vtype):
    if "std::vector" in vtype:
        vtype = vtype[6:]
        index = vtype.find(",")
        vtype = vtype[:index]
        vtype += ">"
    return vtype


def c_process_map(vtype):
    if "std::map" in vtype:
        vtype = vtype[6:]
        index = vtype.find(",")
        end_index = vtype.find(",", index + 1)
        vtype = vtype[:end_index]
        vtype = vtype[:index+1] + " " + vtype[index+1:]
        vtype += ">"
    return vtype


def c_check_var(vtype):
    replace_dict = {
        "class std::basic_string"
        + "<char,struct std::char_traits<char>,"
        + "class std::allocator<char> >": "std::string"
    }
    # check that the type matches any of the keys even if partial
    for key in replace_dict:
        if key in vtype:
            vtype = vtype.replace(key, replace_dict[key])
    if isEnum(vtype):
        vtype = vtype.replace("::Enum", "")
    if isVector(vtype):
        vtype = c_process_vector(vtype)
    if isMap(vtype):
        vtype = c_process_map(vtype)
    return vtype


def c_build_object(component_name, variables):
    if len(variables) == 0:
        return f"struct {component_name} : Component" \
            + " {} //no variables in schema!\n\n"
    total_component_size = 0
    cstring = f"struct {component_name} : Component" + " {\n"
    for var in variables:

        name = var.get("name")
        size = var.get("size")
        bIsEnum = isEnum(var.get("type"))
        total_component_size += int(size)
        vtype = c_check_var(var.get("type"))
        if bIsEnum:
            cstring += f"\t{vtype} {name}; // enum class sizeof = {size};\n"
        else:
            cstring += f"\t{vtype} {name}; // sizeof = {size};\n"
    cstring += "};\n\n"
    return cstring


if len(sys.argv) < 2:
    print("\n\nError - bad args\nUsage: python schema_tool.py <schema.xml>")
    print("to get a schema run 'noita.exe -build_schemas_n_exit'")
    print("browse to the data/schemas/ folder and find the latest file\n\n")
    exit()

xml_schema_file = sys.argv[1]

# process it so there are no invalid xml chars
xml_data = open(xml_schema_file, "r").read()
xml_data = re.sub(pattern, lambda match: match.group(
    0).replace('<', '&lt;').replace('>', '&gt;'), xml_data)

xml_output_file = "processed_latest.xml"
open(xml_output_file, "w").write(xml_data)

tree = ET.parse(xml_output_file)

# delete temp processed file
os.remove(xml_output_file)

root = tree.getroot()
schema_hash = root.get("hash")
components = root.findall("Component")

print(f"Schema hash: {schema_hash}")
print("Found components: ", len(components))
print("Building C++ structs...")

c_output_file = "Components.h"
c_output = open(c_output_file, "w")
for component in components:
    print(f"Building struct for {component.get('component_name')}")
    component_name = component.get("component_name")
    variables = component.findall("Var")
    print(f"Found {len(variables)} variables")
    if len(variables) == 0:
        print("No variables found for component! it will be empty!")
    c_output.write(c_build_object(component_name, variables))
c_output.close()
print(f"Done! C++ structs written to {c_output_file}")

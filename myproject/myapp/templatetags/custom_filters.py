from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    ดึงค่าจาก dictionary ด้วยคีย์ที่กำหนด
    ใช้ในเทมเพลตเช่น: {{ mydict|get_item:item.name }}
    """
    if dictionary is None:
        return None
    
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    
    try:
        return dictionary[key]
    except (KeyError, TypeError):
        return None

@register.filter
def sum_dict_column(data_dict, column_name):
    """
    รวมค่าในคอลัมน์หนึ่งจาก dictionary ของ dictionary
    ใช้ในเทมเพลตเช่น: {{ data_dict|sum_dict_column:"amount" }}
    """
    if not data_dict:
        return 0
    
    total = 0
    for day, values in data_dict.items():
        if values and column_name in values:
            value = values[column_name]
            if value is not None:
                try:
                    total += float(value)
                except (ValueError, TypeError):
                    pass
    
    # คืนค่าเป็นจำนวนเต็มถ้าไม่มีทศนิยม
    if total == int(total):
        return int(total)
    return total
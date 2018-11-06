import argparse
import struct
import math
import os

OFFSET_TO_FIELD_MAP = {
    'bytes_per_sector': (11, 13, '<H'),
    'sectors_per_cluster': (13, 14, '<b'),
    'reserved_sectors_count': (14, 16, '<H'),
    'numbers_of_FAT': (16, 17, '<b'),
    'root_entity_count': (17, 19, '<H'),
    'total_sectors_16': (19, 21, '<H'),
    'media': (21, 22, '<b'),
    'FAT_size': (22, 24, '<H'),
    'sectors_per_track': (24, 26, '<H'),
    'number_of_heads': (26, 28, '<H'),
    'number_of_hidden_sectors': (28, 32, '<I'),
    'total_sectors_32': (32, 36, '<I')
}


def get_boot_sector_params(data: bytes) -> dict:
    boot_sector_params = dict()
    for field_name, value in OFFSET_TO_FIELD_MAP.items():
        start_offset, end_offset, data_format = value
        field_value = struct.unpack(data_format, bytearray(data[start_offset:end_offset]))[0]
        boot_sector_params[field_name] = field_value
    return boot_sector_params


def calculate_parameters(boot_sector_params: dict) -> dict:
    fat_start_sector = boot_sector_params['reserved_sectors_count']
    fat_sectors = boot_sector_params['FAT_size'] * boot_sector_params['numbers_of_FAT']
    root_directory_start_sector = fat_start_sector + fat_sectors
    root_directory_sectors = math.floor((32 * boot_sector_params['root_entity_count'] +
                                         boot_sector_params['bytes_per_sector'] - 1) / boot_sector_params[
                                            'bytes_per_sector'])
    data_start_sector = root_directory_start_sector + root_directory_sectors
    if boot_sector_params['total_sectors_16']:
        data_sectors = boot_sector_params['total_sectors_16'] - data_start_sector
    else:
        data_sectors = boot_sector_params['total_sectors_32'] - data_start_sector
    count_of_clusters = math.floor(data_sectors / boot_sector_params['sectors_per_cluster'])
    calculated_params = locals()
    calculated_params.pop('boot_sector_params')
    return calculated_params


def print_dictionary(dictionary: dict):
    for key, value in dictionary.items():
        print(f"{key} = {value}")


def main(drive_name: str):
    if os.name == 'posix':
        drive = f"/dev/{drive_name}"
    elif os.name == 'nt':
        drive = r'\\.\%s:' % drive_name
    else:
        raise Exception('Not known OS')
    with open(drive, 'rb') as file:
        data = file.read(512)
        boot_sector_params = get_boot_sector_params(data)
        calculated_params = calculate_parameters(boot_sector_params)
        print_dictionary(boot_sector_params)
        print_dictionary(calculated_params)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parsing boot sector in FAT formatted drive", add_help=True)
    parser.add_argument('-d', '--drive', help="drive name", required=False)
    args = parser.parse_args()
    try:
        if not args.drive:
            print(f"Not specified drive name, please check help")
            parser.print_help()
        else:
            main(args.drive)
    except KeyboardInterrupt:
        exit(1)

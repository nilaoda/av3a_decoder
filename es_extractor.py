from tqdm import tqdm
import os
import sys

AV3A_START = bytes.fromhex('FFF2')

def extract_pes_payload(input_file, output_file, pid):
    with open(input_file, 'rb') as f, open(output_file, 'wb') as out_file:
        pes_data = bytearray()

        file_size = os.path.getsize(input_file)
        progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc='Processing', ncols=75)

        while True:
            chunk = f.read(188)
            if not chunk:
                break

            sync_byte = chunk[0]
            if sync_byte == 0x47:
                packet_pid = ((chunk[1] & 0x1F) << 8) + chunk[2]
                if packet_pid == pid:
                    payload_unit_start_indicator = (chunk[1] & 0x40) >> 6
                    adaptation_field_control = (chunk[3] & 0x30) >> 4
                    adaptation_field_length = 0

                    if adaptation_field_control == 3:
                        adaptation_field_length = chunk[4]
                        pes_header_length = 4 + 6 + 1 + adaptation_field_length
                    elif adaptation_field_control == 1:
                        pes_header_length = 4 + 6

                    if payload_unit_start_indicator == 1:
                        to_skip_len = chunk[pes_header_length:].index(AV3A_START)
                        pes_data += chunk[pes_header_length+to_skip_len:]
                    elif adaptation_field_length > 0:
                        pes_data += chunk[4+1+adaptation_field_length:]
                    else:
                        pes_data += chunk[4:]

                    if pes_data:
                        out_file.write(pes_data)
                        pes_data = bytearray()

            progress_bar.update(188)

        if pes_data:
            out_file.write(pes_data)

        progress_bar.close()


if len(sys.argv) < 3:
  sys.exit(-1)

extract_pes_payload(sys.argv[1], sys.argv[2], int(sys.argv[3], 16) if sys.argv[3].startswith('0x') else int(sys.argv[3]))

import argparse
import datetime
import logging
import os
import posixpath
import re
import sys
import time

if len(sys.argv) < 3:
  sys.exit(-1)

from unicorn import *
from unicorn.arm_const import *
from ExAndroidNativeEmu.androidemu.emulator import Emulator
from ExAndroidNativeEmu.androidemu.utils import memory_helpers
from tqdm import tqdm

# logging config
logging.basicConfig(
    stream=sys.stdout,
    level=100,
    #level=5,
    format="%(asctime)s %(levelname)7s %(name)15s | %(message)s"
)

work_dir = os.getcwd()
py_file_path = os.path.dirname(os.path.abspath(__file__))
emu_file_path = posixpath.join(py_file_path, 'ExAndroidNativeEmu')
# switch
os.chdir(emu_file_path)

vfs_root = posixpath.join(emu_file_path, "vfs")
# init
emulator = Emulator(
    vfs_root=vfs_root
)

# load lib
libcm = emulator.load_library(f"{vfs_root}/system/lib/libc.so", do_init=False)
lib_module = emulator.load_library(posixpath.join(py_file_path, "libavs3a_decoder.so"))

# switch
os.chdir(work_dir)

def get_full_path(path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.abspath(path)


in_av3a = sys.argv[1]
out_wav = sys.argv[2]
in_file_path = get_full_path(in_av3a)
out_file_path = get_full_path(out_wav)

print('input', in_file_path)
print('output', out_file_path)
print()

in_file_size = os.path.getsize(in_file_path)
# delete if exists
if os.path.exists(out_file_path):
    os.remove(out_file_path)
# create
open(out_file_path, 'w').close()
argv = ["", in_av3a, out_wav]
argc = len(argv)

# make argv
argv_txt = ''.join(argv)
argv_size = len(argv_txt.encode(encoding="utf-8")) + len(argv)
argv_addr = emulator.call_symbol(libcm, 'malloc', argv_size)
memory_helpers.write_utf8_array(emulator.mu, argv_addr, argv)
cur = argv_addr
argv_ptr_list = [cur]

# make ptr
for v in argv:
    cur = cur + memory_helpers.write_utf8(emulator.mu, cur, v)
    argv_ptr_list.append(cur)

#print(memory_helpers.read_byte_array(emulator.mu, argv_addr, argv_size))

# int[] ptr
argv_addr = emulator.call_symbol(libcm, 'malloc', 4*argc)
memory_helpers.write_uints(emulator.mu, argv_addr, argv_ptr_list)

# data ptr
data_addr = emulator.call_symbol(libcm, 'malloc', 16384*2)

# file ptr
in_file_addr = emulator.call_symbol(libcm, 'malloc', 8)
out_file_addr = emulator.call_symbol(libcm, 'malloc', 8)
model_file_addr = emulator.call_symbol(libcm, 'malloc', 8)

# Decoder Context (unknown struct size)
av3aDec_addr = emulator.call_symbol(libcm, 'malloc', 5000)

# GetAvs3DecoderCommandLine
result = emulator.call_native(lib_module.base + 0x688C + 1, av3aDec_addr, argc, argv_addr, in_file_addr, out_file_addr)

# Print stream info
bit_rate_kbps = int(int.from_bytes(memory_helpers.read_byte_array(emulator.mu, av3aDec_addr + 12, 4), byteorder='little') / 1000)
channels_count = int.from_bytes(memory_helpers.read_byte_array(emulator.mu, av3aDec_addr + 24, 2), byteorder='little')
frame_length = int.from_bytes(memory_helpers.read_byte_array(emulator.mu, av3aDec_addr + 48, 2), byteorder='little')
total_frames = int(in_file_size / frame_length)
print('bit_rate', bit_rate_kbps, 'kbps')
print('channels_count', channels_count)
print('frame_length', frame_length)
print('total_frames', total_frames)
print()

# Avs3InitDecoder
result = emulator.call_native(lib_module.base + 0x60AC + 1, av3aDec_addr, model_file_addr)

# Starting decode
in_file_o = memory_helpers.read_ptr(emulator.mu, in_file_addr)
out_file_o = memory_helpers.read_ptr(emulator.mu, out_file_addr)

with tqdm(total=total_frames, ncols=75, desc='Decoding') as pbar:
    # ReadBitstream
    result = emulator.call_native(lib_module.base + 0x4C52 + 1, av3aDec_addr, in_file_o)
    # see libijkffmpeg.so sub_E1E9E
    stream_ptr = memory_helpers.read_ptr(emulator.mu, av3aDec_addr + 72)
    while result > 0:
      pbar.update(1)
      # Avs3Decode
      emulator.call_native(lib_module.base + 0x5844 + 1, av3aDec_addr, data_addr)
      # ResetBitstream
      emulator.call_native(lib_module.base + 0x4754 + 1, stream_ptr)
      # WriteSynthData
      emulator.call_native(lib_module.base + 0x6950 + 1, data_addr, out_file_o, channels_count, frame_length)
      # ReadBitstream
      result = emulator.call_native(lib_module.base + 0x4C52 + 1, av3aDec_addr, in_file_o)

print()
# SynthWavHeader
emulator.call_native(lib_module.base + 0x6988 + 1, out_file_o)
print('done')

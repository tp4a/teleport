# -*- coding: utf-8 -*-

import ctypes
import os
import struct
from ctypes import windll, wintypes

# FSCTL_GET_REPARSE_POINT = 0x900a8
#
# FILE_ATTRIBUTE_READONLY = 0x0001
# FILE_ATTRIBUTE_HIDDEN = 0x0002
# FILE_ATTRIBUTE_DIRECTORY = 0x0010
# FILE_ATTRIBUTE_NORMAL = 0x0080
FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
#
# GENERIC_READ = 0x80000000
# GENERIC_WRITE = 0x40000000
# OPEN_EXISTING = 3
# FILE_READ_ATTRIBUTES = 0x80
# FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
# INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
#
# INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
#
# # FILE_FLAG_OPEN_REPARSE_POINT = 2097152
# FILE_FLAG_BACKUP_SEMANTICS = 33554432
# # FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTI
# FILE_FLAG_REPARSE_BACKUP = 35651584

GetFileAttributes = windll.kernel32.GetFileAttributesW
# _CreateFileW = windll.kernel32.CreateFileW
# _DevIoCtl = windll.kernel32.DeviceIoControl
# _DevIoCtl.argtypes = [
#     wintypes.HANDLE,  # HANDLE hDevice
#     wintypes.DWORD,  # DWORD dwIoControlCode
#     wintypes.LPVOID,  # LPVOID lpInBuffer
#     wintypes.DWORD,  # DWORD nInBufferSize
#     wintypes.LPVOID,  # LPVOID lpOutBuffer
#     wintypes.DWORD,  # DWORD nOutBufferSize
#     ctypes.POINTER(wintypes.DWORD),  # LPDWORD lpBytesReturned
#     wintypes.LPVOID]  # LPOVERLAPPED lpOverlapped
# _DevIoCtl.restype = wintypes.BOOL


def islink(path):
    assert os.path.isdir(path), path
    if GetFileAttributes(path) & FILE_ATTRIBUTE_REPARSE_POINT:
        return True
    else:
        return False

#
# def DeviceIoControl(hDevice, ioControlCode, input, output):
#     # DeviceIoControl Function
#     # http://msdn.microsoft.com/en-us/library/aa363216(v=vs.85).aspx
#     if input:
#         input_size = len(input)
#     else:
#         input_size = 0
#     if isinstance(output, int):
#         output = ctypes.create_string_buffer(output)
#     output_size = len(output)
#     assert isinstance(output, ctypes.Array)
#     bytesReturned = wintypes.DWORD()
#     status = _DevIoCtl(hDevice, ioControlCode, input,
#                        input_size, output, output_size, bytesReturned, None)
#     print("status(%d)" % status)
#     if status != 0:
#         return output[:bytesReturned.value]
#     else:
#         return None
#
#
# def CreateFile(path, access, sharemode, creation, flags):
#     return _CreateFileW(path, access, sharemode, None, creation, flags, None)
#
#
# SymbolicLinkReparseFormat = "LHHHHHHL"
# SymbolicLinkReparseSize = struct.calcsize(SymbolicLinkReparseFormat);
#
#
# def readlink(path):
#     """ Windows readlink implementation. """
#     # This wouldn't return true if the file didn't exist, as far as I know.
#     assert islink(path)
#     assert type(path) == unicode
#
#     # Open the file correctly depending on the string type.
#     hfile = CreateFile(path, GENERIC_READ, 0, OPEN_EXISTING,
#                        FILE_FLAG_REPARSE_BACKUP)
#     # MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 16384 = (16*1024)
#     buffer = DeviceIoControl(hfile, FSCTL_GET_REPARSE_POINT, None, 16384)
#     CloseHandle(hfile)
#
#     # Minimum possible length (assuming length of the target is bigger than 0)
#     if not buffer or len(buffer) < 9:
#         return None
#
#     # Parse and return our result.
#     # typedef struct _REPARSE_DATA_BUFFER {
#     #   ULONG  ReparseTag;
#     #   USHORT ReparseDataLength;
#     #   USHORT Reserved;
#     #   union {
#     #       struct {
#     #           USHORT SubstituteNameOffset;
#     #           USHORT SubstituteNameLength;
#     #           USHORT PrintNameOffset;
#     #           USHORT PrintNameLength;
#     #           ULONG Flags;
#     #           WCHAR PathBuffer[1];
#     #       } SymbolicLinkReparseBuffer;
#     #       struct {
#     #           USHORT SubstituteNameOffset;
#     #           USHORT SubstituteNameLength;
#     #           USHORT PrintNameOffset;
#     #           USHORT PrintNameLength;
#     #           WCHAR PathBuffer[1];
#     #       } MountPointReparseBuffer;
#     #       struct {
#     #           UCHAR  DataBuffer[1];
#     #       } GenericReparseBuffer;
#     #   } DUMMYUNIONNAME;
#     # } REPARSE_DATA_BUFFER, *PREPARSE_DATA_BUFFER;
#
#     # Only handle SymbolicLinkReparseBuffer
#     (tag, dataLength, reserver, SubstituteNameOffset, SubstituteNameLength,
#      PrintNameOffset, PrintNameLength,
#      Flags) = struct.unpack(SymbolicLinkReparseFormat,
#                             buffer[:SymbolicLinkReparseSize])
#     print(tag, dataLength, reserver, SubstituteNameOffset, SubstituteNameLength)
#     start = SubstituteNameOffset + SymbolicLinkReparseSize
#     actualPath = buffer[start: start + SubstituteNameLength].decode("utf-16")
#     # This utf-16 string is null terminated
#     index = actualPath.find(u"\0")
#     assert index > 0
#     if index > 0:
#         actualPath = actualPath[:index]
#     if actualPath.startswith(u"?\\"):
#         return actualPath[2:]
#     else:
#         return actualPath


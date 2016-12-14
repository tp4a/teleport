# -*- coding: utf-8 -*-
import zipfile
import os


# class ZFile(object):
#     def __init__(self, filename, mode='r', basedir=''):
#         self.filename = filename
#         self.mode = mode
#         if self.mode in ('w', 'a'):
#             self.zfile = zipfile.ZipFile(filename, self.mode, compression=zipfile.ZIP_DEFLATED)
#         else:
#             self.zfile = zipfile.ZipFile(filename, self.mode)
#         self.basedir = basedir
#         if not self.basedir:
#             self.basedir = os.path.dirname(filename)
#
#     def addfile(self, path, arcname=None):
#         path = path.replace('//', '/')
#         if not arcname:
#             if path.startswith(self.basedir):
#                 arcname = path[len(self.basedir):]
#             else:
#                 arcname = ''
#         self.zfile.write(path, arcname)
#
#     def addfiles(self, paths):
#         for path in paths:
#             if isinstance(path, tuple):
#                 self.addfile(*path)
#             else:
#                 self.addfile(path)
#
#     def close(self):
#         self.zfile.close()
#
#     def extract_to(self, path):
#         for p in self.zfile.namelist():
#             self.extract(p, path)
#
#     def extract(self, filename, path):
#         if not filename.endswith('/'):
#             strtemp = type(filename)
#             # filename = filename.encode()
#             # filename = filename.decode('gbk')
#             # filename.
#             if sys.getfilesystemencoding() == 'mbcs':
#                 filename = filename.decode('mbcs')
#             f = os.path.join(path, filename)
#             dir = os.path.dirname(f)
#             if not os.path.exists(dir):
#                 os.makedirs(dir)
#             # file(f, 'wb').write(self.zfile.read(filename))
#             file_object = open(f, 'wb')
#             file_object.write(self.zfile.read(filename))
#             file_object.close()
#
#
# def create(zfile, files):
#     z = ZFile(zfile, 'w')
#     z.addfiles(files)
#     z.close()
#
#
# def extract(zfile, path):
#     z = ZFile(zfile)
#     z.extract_to(path)
#     z.close()


def zip_dir(dirname, zipfilename):
    ret = False
    filelist = []
    if os.path.isfile(dirname):
        item = os.path.split(dirname)
        dirname = item[0]
        root = dirname
        name = item[1]
        filelist.append(os.path.join(root, name))
    else:
        for root, dirs, files in os.walk(dirname):
            for name in files:
                filelist.append(os.path.join(root, name))

    if os.path.exists(zipfilename):
        os.remove(zipfilename)

    zf = zipfile.ZipFile(zipfilename, "w", zipfile.zlib.DEFLATED)
    try:
        for tar in filelist:
            arcname = tar[len(dirname):]
            # print arcname
            zf.write(tar, arcname)
        ret = True
    except Exception as e:
        ret = False
    finally:
        zf.close()
        return ret


def unzip_file(zipfilename, unziptodir):
    ret = False
    if not os.path.exists(unziptodir):
        os.makedirs(unziptodir, 0o777)

    zfobj = zipfile.ZipFile(zipfilename)
    try:
        for name in zfobj.namelist():
            name = name.replace('\\', '/')

            if name.endswith('/'):
                os.mkdir(os.path.join(unziptodir, name))
            else:
                ext_filename = os.path.join(unziptodir, name)
                ext_dir = os.path.dirname(ext_filename)
                if not os.path.exists(ext_dir):
                    os.mkdir(ext_dir, 0o777)
                outfile = open(ext_filename, 'wb')
                outfile.write(zfobj.read(name))
                outfile.close()
        ret = True
    except Exception as e:
        ret = False
    finally:
        zfobj.close()
        return ret

# if __name__ == '__main__':
#     try:
#         # create('d:\\5.zip', 'd:\\1\\2.txt')
#         # zip_dir('d:\\1\\', 'd:\\5.zip')
#         # zip_dir('d:\\1\\2.txt', 'd:\\5.zip')
#         unzip_file('d:\\5.zip', 'c:\\3\\3\\')
#         # temp = sys.getfilesystemencoding()
#         # extract('d:\\1.zip','c:\\')
#     except Exception as e:
#         temp = str(e)
#         pass

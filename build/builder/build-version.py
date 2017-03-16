#!/bin/env python3
# -*- coding: utf-8 -*-

import codecs

from core import colorconsole as cc
from core import utils
from core.env import env
from core.context import *

ctx = BuildContext()


# ROOT_PATH = utils.cfg.ROOT_PATH


class Builder:
    def __init__(self):
        self.ver_in = os.path.join(env.root_path, 'version.in')

        self.VER_TELEPORT_SERVER = ''
        self.VER_TELEPORT_ASSIST = ''
        self.VER_TELEPORT_ASSIST_REQUIRE = ''
        # self.VER_TELEPORT_MAKECERT = ''

    def build(self):
        cc.n('update version...')

        if not os.path.exists(self.ver_in):
            raise RuntimeError('file `version.in` not exists.')
        with codecs.open(self.ver_in, 'r', 'utf-8') as f:
            lines = f.readlines()
            for l in lines:
                if l.startswith('TELEPORT_SERVER '):
                    x = l.split(' ')
                    self.VER_TELEPORT_SERVER = x[1].strip()
                elif l.startswith('TELEPORT_ASSIST '):
                    x = l.split(' ')
                    self.VER_TELEPORT_ASSIST = x[1].strip()
                elif l.startswith('TELEPORT_ASSIST_REQUIRE '):
                    x = l.split(' ')
                    self.VER_TELEPORT_ASSIST_REQUIRE = x[1].strip()
                    # elif l.startswith('TELEPORT_MAKECERT '):
                    #     x = l.split(' ')
                    #     self.VER_TELEPORT_MAKECERT = x[1].strip()

        #
        cc.v('new version:')
        cc.v('  TELEPORT-Server         : ', self.VER_TELEPORT_SERVER)
        cc.v('  TELEPORT-Assist         : ', self.VER_TELEPORT_ASSIST)
        cc.v('  TELEPORT-Assist-require : ', self.VER_TELEPORT_ASSIST_REQUIRE)
        # cc.v('  TELEPORT-MakeCert       : ', self.VER_TELEPORT_MAKECERT)
        cc.v('')

        self.make_build_ver()
        self.make_assist_ver()
        self.make_tp_core_ver()
        self.make_tp_web_ver()
        self.make_web_ver()

    def make_build_ver(self):
        ver_file = os.path.join(env.root_path, 'build', 'builder', 'core', 'ver.py')
        # ver_content = '# -*- coding: utf8 -*-\nVER_TELEPORT_SERVER = "{}"\nVER_TELEPORT_ASSIST = "{}"\nVER_TELEPORT_MAKECERT = "{}"\n'.format(self.VER_TELEPORT_SERVER, self.VER_TELEPORT_ASSIST, self.VER_TELEPORT_MAKECERT)
        ver_content = '# -*- coding: utf8 -*-\nVER_TELEPORT_SERVER = "{}"\nVER_TELEPORT_ASSIST = "{}"\n'.format(self.VER_TELEPORT_SERVER, self.VER_TELEPORT_ASSIST)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            old_content = ''
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

    def make_web_ver(self):
        ver_file = os.path.join(env.root_path, 'server', 'www', 'teleport', 'app', 'eom_ver.py')
        # ver_content = '# -*- coding: utf8 -*-\n\nTS_VER = "{}"\n'.format(self.VER_TELEPORT_SERVER)
        ver_content = '# -*- coding: utf8 -*-\nTS_VER = "{}"\nTP_ASSIST_LAST_VER = "{}"\nTP_ASSIST_REQUIRE = "{}"\n'.format(self.VER_TELEPORT_SERVER, self.VER_TELEPORT_ASSIST, self.VER_TELEPORT_ASSIST_REQUIRE)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            old_content = ''
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

    def make_assist_ver(self):
        ver_file = os.path.join(env.root_path, 'client', 'tp_assist', 'ts_ver.h')
        ver_content = '#ifndef __TS_ASSIST_VER_H__\n#define __TS_ASSIST_VER_H__\n\n#define TP_ASSIST_VER\tL"{}"\n\n#endif // __TS_ASSIST_VER_H__\n'.format(self.VER_TELEPORT_ASSIST)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            old_content = ''
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

        rc_file = os.path.join(env.root_path, 'client', 'tp_assist', 'tp_assist.rc')
        self._update_vs_rc(rc_file, self.VER_TELEPORT_ASSIST)

        nsi_file = os.path.join(env.root_path, 'dist', 'windows', 'client', 'assist', 'installer.nsi')
        self._update_nsi_rc(nsi_file, self.VER_TELEPORT_ASSIST)

    def make_tp_core_ver(self):
        ver_file = os.path.join(env.root_path, 'server', 'tp_core', 'core', 'ts_ver.h')
        ver_content = '#ifndef __TS_SERVER_VER_H__\n#define __TS_SERVER_VER_H__\n\n#define TP_SERVER_VER\tL"{}"\n\n#endif // __TS_SERVER_VER_H__\n'.format(self.VER_TELEPORT_SERVER)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            old_content = ''
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

        rc_file = os.path.join(env.root_path, 'server', 'tp_core', 'core', 'tp_core.rc')
        self._update_vs_rc(rc_file, self.VER_TELEPORT_SERVER)

    def make_tp_web_ver(self):
        ver_file = os.path.join(env.root_path, 'server', 'tp_web', 'src', 'ts_ver.h')
        ver_content = '#ifndef __TS_SERVER_VER_H__\n#define __TS_SERVER_VER_H__\n\n#define TP_SERVER_VER\tL"{}"\n\n#endif // __TS_SERVER_VER_H__\n'.format(self.VER_TELEPORT_SERVER)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            old_content = ''
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

        rc_file = os.path.join(env.root_path, 'server', 'tp_web', 'src', 'tp_web.rc')
        self._update_vs_rc(rc_file, self.VER_TELEPORT_SERVER)

    def _update_vs_rc(self, rcFilePath, ver):
        """ update rc file version info """

        t_ver = ver.split('.')
        if len(t_ver) != 4:
            raise RuntimeError('Invalid version for assist.')

        bOK = False
        try:
            # open rc file
            rcFile = codecs.open(rcFilePath, 'r', 'utf16')
            # read out all lines of rc file
            rcLines = rcFile.readlines()
            rcFile.close()

            for x in range(len(rcLines)):
                rcline = rcLines[x]

                if rcline.find(" FILEVERSION") != -1:  # find " FILEVERSION"
                    # cc.v('[ver] old ver:  %s' % rcLines[x])
                    pos1 = rcline.find(' FILEVERSION ')
                    pos2 = rcline.rfind('\\0"')
                    _ver = rcline[pos1 + 13: pos2].strip()

                    rcSplitList = _ver.split(",")
                    if (len(rcSplitList) < 4):
                        rcSplitList = _ver.split(".")
                    if (len(rcSplitList) < 4):
                        raise RuntimeError('Invalid .rc file.')
                    if '.'.join(rcSplitList) == ver:
                        continue

                    rcline = '%s%s,%s,%s,%s\n' % (rcline[0:pos1 + 13], t_ver[0], t_ver[1], t_ver[2], t_ver[3])

                    rcLines[x] = ""
                    rcLines[x] = rcline
                    # cc.v('[ver] new ver:  %s' % rcLines[x])
                    bOK = True

                elif rcline.find("VALUE \"FileVersion\",") != -1:  # find "VALUE FileVersion"
                    # cc.v('[ver] old ver:  %s' % rcLines[x])
                    pos1 = rcline.find('\"FileVersion\", \"')
                    pos2 = rcline.rfind('\\0"')
                    _ver = rcline[pos1 + 16: pos2].strip()

                    rcSplitList = _ver.split(".")
                    if (len(rcSplitList) < 4):
                        rcSplitList = _ver.split(",")
                    if (len(rcSplitList) < 4):
                        raise RuntimeError('Invalid .rc file.')
                    if '.'.join(rcSplitList) == ver:
                        continue

                    rcline = '%s%s.%s.%s.%s\\0\"\n' % (rcline[0:pos1 + 16], t_ver[0], t_ver[1], t_ver[2], t_ver[3])

                    rcLines[x] = ""
                    rcLines[x] = rcline
                    # cc.v('[ver] new ver:  %s' % rcLines[x])
                    bOK = True

                elif rcline.find(" PRODUCTVERSION") != -1:
                    # cc.v('[ver] old ver:  %s' % rcLines[x])
                    pos1 = rcline.find(' PRODUCTVERSION ')
                    pos2 = rcline.rfind('\\0"')
                    _ver = rcline[pos1 + 16: pos2].strip()

                    rcSplitList = _ver.split(",")
                    if (len(rcSplitList) < 4):
                        rcSplitList = _ver.split(".")
                    if (len(rcSplitList) < 4):
                        raise RuntimeError('Invalid .rc file.')
                    if '.'.join(rcSplitList) == ver:
                        continue

                    rcline = '%s%s,%s,%s,%s\n' % (rcline[0:pos1 + 16], t_ver[0], t_ver[1], t_ver[2], t_ver[3])

                    rcLines[x] = ""
                    rcLines[x] = rcline
                    # cc.v('[ver] new ver:  %s' % rcLines[x])
                    bOK = True

                elif rcline.find("VALUE \"ProductVersion\",") != -1:
                    # cc.v('[ver] old ver:  %s' % rcLines[x])
                    pos1 = rcline.find('\"ProductVersion\", \"')
                    pos2 = rcline.rfind('\\0"')
                    _ver = rcline[pos1 + 19: pos2].strip()

                    rcSplitList = _ver.split(".")
                    if (len(rcSplitList) < 4):
                        rcSplitList = _ver.split(",")
                    if (len(rcSplitList) < 4):
                        raise RuntimeError('Invalid .rc file.')
                    if '.'.join(rcSplitList) == ver:
                        continue

                    rcline = '%s%s.%s.%s.%s\\0\"\n' % (rcline[0:pos1 + 19], t_ver[0], t_ver[1], t_ver[2], t_ver[3])

                    rcLines[x] = ""
                    rcLines[x] = rcline
                    # cc.v('[ver] new ver:  %s' % rcLines[x])
                    bOK = True

            if bOK:
                cc.v('  update {}...'.format(rcFilePath))
                wrcFile = codecs.open(rcFilePath, 'w', 'utf16')
                wrcFile.writelines(rcLines)
                wrcFile.close()

        except IOError:
            raise RuntimeError('can not open rc file.')

    def _update_nsi_rc(self, nsiFilePath, ver):
        """ update nsis file version info """
        # nver = ver.split('.')
        t_ver = ver.split('.')
        if len(t_ver) != 4:
            raise RuntimeError('Invalid version for assist.')

        bOK = False
        try:
            # open nsis file
            nsiFile = open(nsiFilePath, 'r', encoding='utf-16-le')
            # read out all lines of nsi file
            nsiLines = nsiFile.readlines()
            nsiFile.close()

            # for nsiline in nsiLines:
            for x in range(len(nsiLines)):
                nsiline = nsiLines[x]
                if nsiline.find('\n') != -1:
                    nsiline = nsiline[:-1]

                if nsiline.find(" FILE_VER") != -1 or nsiline.find(" STR_FILE_VER") != -1:
                    # cc.v('[ver] old ver:  %s' % nsiLines[x])
                    pos1 = nsiline.find('"')
                    pos2 = nsiline.rfind('"')
                    _ver = nsiline[pos1 + 1: pos2]

                    nsiSplitList = _ver.split(".")
                    if (len(nsiSplitList) != 4):
                        raise RuntimeError('Invalid .nsi file (1).')
                    if '.'.join(nsiSplitList) == ver:
                        continue

                    # nsiline = '%s\"%d.%d.%d.%d\"\n' % (nsiline[0:pos1], self.major, self.minor, self.revision, self.build)
                    nsiline = '%s\"%s.%s.%s.%s\"\n' % (nsiline[0:pos1], t_ver[0], t_ver[1], t_ver[2], t_ver[3])

                    nsiLines[x] = ""
                    nsiLines[x] = nsiline
                    # cc.v('[ver] new ver:  %s' % nsiLines[x])
                    bOK = True

                elif nsiline.find(" PRODUCT_VER") != -1:
                    # cc.v('[ver] old ver:  %s' % nsiLines[x])
                    pos1 = nsiline.find('"')
                    pos2 = nsiline.rfind('"')
                    _ver = nsiline[pos1 + 1: pos2]

                    nsiSplitList = _ver.split(".")
                    if (len(nsiSplitList) != 2):
                        raise RuntimeError('Invalid .nsi file (2).')
                    if '.'.join(nsiSplitList) == '%s.%s' % (t_ver[0], t_ver[1]):
                        continue

                    # nsiline = '%s\"%d.%d\"\n' % (nsiline[0:pos1], self.major, self.minor)
                    nsiline = '%s\"%s.%s\"\n' % (nsiline[0:pos1], t_ver[0], t_ver[1])

                    nsiLines[x] = ""
                    nsiLines[x] = nsiline
                    # cc.v('[ver] new ver:  %s' % nsiLines[x])
                    bOK = True

                else:
                    continue

            if bOK:
                cc.v('  update {}...'.format(nsiFilePath))
                wnsiFile = open(nsiFilePath, 'w', encoding='utf-16-le')
                wnsiFile.writelines(nsiLines)
                wnsiFile.close()
            return bOK

        except IOError:
            raise RuntimeError('can not open nsi file.')


def main():
    if not env.init():
        return

    builder = Builder()
    builder.build()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        cc.e(e.__str__())
    except:
        cc.f('got exception.')

#!/bin/env python3
# -*- coding: utf-8 -*-

import codecs

from core import colorconsole as cc
from core import utils
from core.context import *

ctx = BuildContext()

ROOT_PATH = utils.cfg.ROOT_PATH


class Builder:
    def __init__(self):
        self.ver_in = os.path.join(ROOT_PATH, 'version.in')

        self.VER_TELEPORT_SERVER = ''
        self.VER_TELEPORT_ASSIST = ''
        self.VER_TELEPORT_ASSIST_REQUIRE = ''
        self.VER_TELEPORT_MAKECERT = ''

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
                elif l.startswith('TELEPORT_MAKECERT '):
                    x = l.split(' ')
                    self.VER_TELEPORT_MAKECERT = x[1].strip()

        #
        cc.v('new version:')
        cc.v('  TELEPORT-Server         : ', self.VER_TELEPORT_SERVER)
        cc.v('  TELEPORT-Assist         : ', self.VER_TELEPORT_ASSIST)
        cc.v('  TELEPORT-Assist-require : ', self.VER_TELEPORT_ASSIST_REQUIRE)
        cc.v('  TELEPORT-MakeCert       : ', self.VER_TELEPORT_MAKECERT)
        cc.v('')

        self.make_build_ver()
        self.make_assist_ver()
        self.make_eom_ts_ver()
        self.make_web_ver()

    def make_build_ver(self):
        ver_file = os.path.join(ROOT_PATH, 'build', 'builder', 'core', 'ver.py')
        ver_content = '# -*- coding: utf8 -*-\nVER_TELEPORT_SERVER = "{}"\nVER_TELEPORT_ASSIST = "{}"\nVER_TELEPORT_MAKECERT = "{}"\n'.format(self.VER_TELEPORT_SERVER, self.VER_TELEPORT_ASSIST, self.VER_TELEPORT_MAKECERT)

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
        ver_file = os.path.join(ROOT_PATH, 'web', 'site', 'teleport', 'app', 'eom_ver.py')
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
        ver_file = os.path.join(ROOT_PATH, 'tp_assist', 'ts_ver.h')
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

        rc_file = os.path.join(ROOT_PATH, 'tp_assist', 'tp_assist.rc')
        self._update_vs_rc(rc_file, self.VER_TELEPORT_ASSIST)

    def make_eom_ts_ver(self):
        ver_file = os.path.join(ROOT_PATH, 'teleport-server', 'src', 'ts_ver.h')
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

        rc_file = os.path.join(ROOT_PATH, 'teleport-server', 'src', 'eom_ts.rc')
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


def main():
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

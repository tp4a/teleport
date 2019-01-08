#!/bin/env python3
# -*- coding: utf-8 -*-

import codecs

from core import colorconsole as cc
from core.context import *
from core.env import env

ctx = BuildContext()


class Builder:
    def __init__(self):
        self.ver_in = os.path.join(env.root_path, 'version.in')

        self.VER_TP_SERVER = ''
        self.VER_TP_TPCORE = ''
        self.VER_TP_TPWEB = ''
        self.VER_TP_ASSIST = ''

    def build(self):
        cc.n('update version...')

        if not os.path.exists(self.ver_in):
            raise RuntimeError('file `version.in` not exists.')
        with codecs.open(self.ver_in, 'r', 'utf-8') as f:
            lines = f.readlines()
            for l in lines:
                if l.startswith('TP_SERVER '):
                    x = l.split(' ')
                    self.VER_TP_SERVER = x[1].strip()
                    # self.VER_TP_SERVER += '.0'
                elif l.startswith('TP_TPCORE '):
                    x = l.split(' ')
                    self.VER_TP_TPCORE = x[1].strip()
                    # self.VER_TP_TPCORE += '.0'
                elif l.startswith('TP_TPWEB '):
                    x = l.split(' ')
                    self.VER_TP_TPWEB = x[1].strip()
                    # self.VER_TP_TPWEB += '.0'
                elif l.startswith('TP_ASSIST '):
                    x = l.split(' ')
                    self.VER_TP_ASSIST = x[1].strip()
                    # self.VER_TP_ASSIST += '.0'

        cc.v('new version:')
        cc.v('  Server             : ', self.VER_TP_SERVER)
        cc.v('    - tp_core        : ', self.VER_TP_TPCORE)
        cc.v('    - tp_web         : ', self.VER_TP_TPWEB)
        cc.v('  Assist             : ', self.VER_TP_ASSIST)
        cc.v('')

        self.make_builder_ver()
        self.make_server_ver()
        self.make_tpcore_ver()
        self.make_tpweb_ver()
        self.make_assist_win_ver()
        self.make_assist_macos_ver()

    def make_builder_ver(self):
        ver_file = os.path.join(env.root_path, 'build', 'builder', 'core', 'ver.py')
        ver_content = '# -*- coding: utf8 -*-\nVER_TP_SERVER = "{}"\nVER_TP_ASSIST = "{}"\n'.format(self.VER_TP_SERVER, self.VER_TP_ASSIST)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

    def make_tpcore_ver(self):
        ver_file = os.path.join(env.root_path, 'server', 'tp_core', 'core', 'ts_ver.h')
        ver_content = '#ifndef __TS_SERVER_VER_H__\n#define __TS_SERVER_VER_H__\n\n#define TP_SERVER_VER\tL"{}"\n\n#endif // __TS_SERVER_VER_H__\n'.format(self.VER_TP_TPCORE)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

        rc_file = os.path.join(env.root_path, 'server', 'tp_core', 'core', 'tp_core.rc')
        self._update_ver_rc(rc_file, self.VER_TP_TPCORE)

    def make_server_ver(self):
        ver_file = os.path.join(env.root_path, 'server', 'www', 'teleport', 'webroot', 'app', 'app_ver.py')
        # ver_content = '# -*- coding: utf8 -*-\n\nTS_VER = "{}"\n'.format(self.VER_TELEPORT_SERVER)
        ver_content = '# -*- coding: utf8 -*-\nTP_SERVER_VER = "{}"\n'.format(self.VER_TP_SERVER)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

    def make_assist_win_ver(self):
        ver_file = os.path.join(env.root_path, 'client', 'tp_assist_win', 'ts_ver.h')
        ver_content = '#ifndef __TS_ASSIST_VER_H__\n#define __TS_ASSIST_VER_H__\n\n#define TP_ASSIST_VER\tL"{}"\n\n#endif // __TS_ASSIST_VER_H__\n'.format(self.VER_TP_ASSIST)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

        rc_file = os.path.join(env.root_path, 'client', 'tp_assist_win', 'tp_assist.rc')
        self._update_ver_rc(rc_file, self.VER_TP_ASSIST)

        nsi_file = os.path.join(env.root_path, 'dist', 'client', 'windows', 'assist', 'installer.nsi')
        self._update_ver_nsi(nsi_file, self.VER_TP_ASSIST)

    def make_assist_macos_ver(self):
        plist_file = os.path.join(env.root_path, 'client', 'tp_assist_macos', 'src', 'TP-Assist-Info.plist')
        self._update_ver_plist(plist_file, self.VER_TP_ASSIST)

        ver_file = os.path.join(env.root_path, 'client', 'tp_assist_macos', 'src', 'csrc', 'ts_ver.h')
        ver_content = '#ifndef __TS_ASSIST_VER_H__\n#define __TS_ASSIST_VER_H__\n\n#define TP_ASSIST_VER\tL"{}"\n\n#endif // __TS_ASSIST_VER_H__\n'.format(self.VER_TP_ASSIST)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

    def make_tpweb_ver(self):
        ver_file = os.path.join(env.root_path, 'server', 'tp_web', 'src', 'ts_ver.h')
        ver_content = '#ifndef __TS_SERVER_VER_H__\n#define __TS_SERVER_VER_H__\n\n#define TP_SERVER_VER\tL"{}"\n\n#endif // __TS_SERVER_VER_H__\n'.format(self.VER_TP_TPWEB)

        rewrite = False
        if not os.path.exists(ver_file):
            rewrite = True
        else:
            with open(ver_file, 'r') as f:
                old_content = f.read()
            if old_content != ver_content:
                rewrite = True

        if rewrite:
            cc.v('  update {}...'.format(ver_file))
            with open(ver_file, 'w') as f:
                f.write(ver_content)

        rc_file = os.path.join(env.root_path, 'server', 'tp_web', 'src', 'tp_web.rc')
        self._update_ver_rc(rc_file, self.VER_TP_TPWEB)

    def _update_ver_rc(self, rcFilePath, ver):
        """ update rc file version info """

        t_ver = ver.split('.')
        while len(t_ver) < 4:
            t_ver.append('0')

        if len(t_ver) > 4:
            raise RuntimeError('Invalid version for .rc file.')

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
            raise RuntimeError('can not process rc file.')

    def _update_ver_nsi(self, nsiFilePath, ver):
        """ update nsis file version info """
        t_ver = ver.split('.')
        while len(t_ver) < 3:
            t_ver.append('0')

        if len(t_ver) > 3:
            raise RuntimeError('Invalid version for nsis file.')

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

                if nsiline.startswith("!define FILE_VER"):
                    nsiline = '!define FILE_VER \"%s.%s.%s.0\"\n' % (t_ver[0], t_ver[1], t_ver[2])

                    nsiLines[x] = ""
                    nsiLines[x] = nsiline
                    # cc.v('[ver] new ver:  %s' % nsiLines[x])
                    bOK = True

                elif nsiline.startswith("!define OUT_VER"):
                    nsiline = '!define OUT_VER \"%s.%s.%s\"\n' % (t_ver[0], t_ver[1], t_ver[2])

                    nsiLines[x] = ""
                    nsiLines[x] = nsiline
                    # cc.v('[ver] new ver:  %s' % nsiLines[x])
                    bOK = True
                elif nsiline.startswith("!define PRODUCT_VER"):
                    nsiline = '!define PRODUCT_VER \"%s.%s\"\n' % (t_ver[0], t_ver[1])

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
            raise RuntimeError('can not process nsi file.')

    def _update_ver_plist(self, plist_file, ver):
        """ update plist file version info for MacOS app."""
        t_ver = ver.split('.')
        if len(t_ver) < 3:
            raise RuntimeError('Invalid version for plist file.')

        bOK = False
        try:
            # open rc file
            f = codecs.open(plist_file, 'r', 'utf8')
            # read out all lines of rc file
            lines = f.readlines()
            f.close()

            is_ver = False
            for x in range(len(lines)):
                l = lines[x]

                if l.find('<key>CFBundleShortVersionString</key>') != -1:
                    is_ver = True
                    continue
                if l.find('<key>CFBundleVersion</key>') != -1:
                    is_ver = True
                    continue

                if is_ver:
                    is_ver = False

                    pos1 = l.find('<string>')
                    pos2 = l.rfind('</string>')
                    if pos1 == -1 or pos2 == -2:
                        continue
                    _ver = l[pos1 + 8: pos2].strip()

                    v = _ver.split(".")
                    if len(v) < 3:
                        raise RuntimeError('Invalid .plist file.')
                    old_ver = '.'.join(v)
                    if old_ver == ver:
                        continue
                    lines[x] = '\t<string>{ver}</string>\n'.format(ver=ver)
                    bOK = True

            if bOK:
                cc.v('  update {}...'.format(plist_file))
                wrcFile = codecs.open(plist_file, 'w', 'utf8')
                wrcFile.writelines(lines)
                wrcFile.close()

        except IOError:
            raise RuntimeError('can not process plist file.')


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

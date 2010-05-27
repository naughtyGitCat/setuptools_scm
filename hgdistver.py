import os
import commands
import subprocess

def version_from_cachefile(cachefile=None):
    if not cachefile:
        return
    #replaces 'with open()' from py2.6
    fd = open(cachefile)
    fd.readline() # remove the comment
    version = None
    try:
        line = fd.readline()
        version_string = line.split(' = ')[1].strip()
        version = version_string[1:-1].decode('string-escape')
    except: # any error means invalid cachefile
        pass
    fd.close()
    return version

def version_from_hg_id(cachefile=None):
    """stolen logic from mercurials setup.py as well"""
    if os.path.isdir('.hg'):
        l = commands.getoutput('hg id -i -t').strip().split()
        while len(l) > 1 and l[-1][0].isalpha(): # remove non-numbered tags
            l.pop()
        if len(l) > 1: # tag found
            version = l[-1]
            if l[0].endswith('+'): # propagate the dirty status to the tag
                version += '+'
            return version

def version_from_hg15_parents(cachefile=None):
    if os.path.isdir('.hg'):
        node = commands.getoutput('hg id -i')

        cmd = 'hg parents --template "{latesttag} {latesttagdistance}'
        out = commands.getoutput(cmd)
        try:
            tag, dist = out.split()
            if tag=='null':
                tag = '0.0'
            return '%s.dev%s-%s' % (tag, dist, node)
        except ValueError:
            pass # unpacking failed, old hg

def version_from_hg_log_with_tags(cachefile=None):
    if os.path.isdir('.hg'):
        node = commands.getoutput('hg id -i')
        cmd = r'hg log -r %s:0 --template "{tags}\n"'
        cmd = cmd % node.rstrip('+')
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        dist = -1 # no revs vs one rev is tricky

        for dist, line in enumerate(proc.stdout):
            tags = [t for t in line.split() if not t.isalpha()]
            if tags:
                return '%s.dev%s-%s' % (tags[0], dist, node)

        return  '0.0.dev%s-%s' % (dist+1, node)

def _archival_to_version(data):
    """stolen logic from mercurials setup.py"""
    if 'tag' in data:
        return data['tag']
    elif 'latesttag' in data:
        return '%(latesttag)s.dev%(latesttagdistance)s-%(node).12s' % data
    else:
        return data.get('node', '')[:12]

def _data_from_archival(path):
    import email
    data = email.message_from_file(open(str(path)))
    return dict(data.items())

def version_from_archival(cachefile=None):
    #XXX: asumes cwd is repo root
    if os.path.exists('.hg_archival.txt'):
        data = _data_from_archival('.hg_archival.txt')
        return _archival_to_version(data)

def version_from_sdist_pkginfo(cachefile=None):
    if cachefile is None and os.path.exists('PKG-INFO'):
        data = _data_from_archival('PKG-INFO')
        version = data.get('Version')
        if version != 'UNKNOWN':
            return version

def write_cachefile(path, version):
    fd = open(path, 'w')
    try:
        fd.write('# this file is autogenerated by hgdistver + setup.py\n')
        fd.write('version = %r' % version)
    finally:
        fd.close()


methods = [
    version_from_hg_id,
    version_from_hg15_parents,
    version_from_hg_log_with_tags,
    version_from_archival,
    version_from_cachefile,
    version_from_sdist_pkginfo,
]

def get_version(cachefile=None):
    try:
        version = None
        for method in methods:
            version = method(cachefile=cachefile)
            if version:
                if version.endswith('+'):
                    import time
                    version += time.strftime('%Y%m%d')
                return version
    finally:
        if cachefile and version:
            write_cachefile(cachefile, version)

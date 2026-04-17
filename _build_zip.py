import os
import zipfile

OUT = 'unity_rig.zip'
if os.path.exists(OUT):
    os.remove(OUT)

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk('unity_rig'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if f.endswith('.pyc'):
                continue
            path = os.path.join(root, f)
            arc = path.replace(os.sep, '/')
            z.write(path, arc)

print('built:', OUT, os.path.getsize(OUT), 'bytes')

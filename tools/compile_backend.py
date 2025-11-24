import py_compile, pathlib, sys
errs = []
for p in pathlib.Path('backend').rglob('*.py'):
    try:
        py_compile.compile(str(p), doraise=True)
        print('OK:', p)
    except Exception as e:
        print('ERR:', p, e)
        errs.append((p, e))
if errs:
    sys.exit(2)
else:
    sys.exit(0)

#!/usr/bin/env python3
import os
import time
from google.cloud import firestore

def main():
    project = os.environ.get('PROJECT_ID')
    db = firestore.Client(project=project)
    col = db.collection('ci_cd_smoke')
    doc = col.document('gitlab_wif_check')
    doc.set({'ok': True, 'ts': time.time()})
    data = doc.get().to_dict()
    assert data and data.get('ok') is True
    print('Firestore write/read OK')

if __name__ == '__main__':
    main()

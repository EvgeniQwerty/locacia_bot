import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
ref = db.collection('Visitors1')
ref = ref.document('Test')
ref.set({
                'ID': 1,
                'Name': 'dfdd'
            })
#docs = ref.get()

'''
for doc in docs:
    id = 0
    name = ''
    id_name = ''
    for key, value in doc.to_dict().items():
        if key == 'ID':
            id = value
        elif key == 'Name':
            name = value
    id_name += '{} - {}\n'.format(id, name)
    print(id_name)
'''
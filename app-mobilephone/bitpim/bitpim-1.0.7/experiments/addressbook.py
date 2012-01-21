from appscript import app, its, k

myABook = app("Address Book.app")

me = myABook.my_card
abMe = me.get()

print abMe.name.get()

for person in myABook.people.get():
  abMe = person.get()
  print abMe.name.get()
  for addr in abMe.addresses.get():
    print addr.label.get(),":\n", addr.street.get(), "\n"
    print addr.city.get(), ",", addr.state.get()," ", addr.zip.get()

  for eml in abMe.emails.get():
    print eml.label.get(),": ", eml.value.get()

  for phn in abMe.phones.get():
    print phn.label.get(),": ",phn.value.get()

  print "-----------------------------"

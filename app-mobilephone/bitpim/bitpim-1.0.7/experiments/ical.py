from appscript import app, its, k
import LaunchServices
import datetime

myical = app('iCal.app')
# myical.activate()

ourCal=0
sga=myical.calendars.filter(its.title=="N9YTY")

myEvent=sga.events.end.make(new=k.event)
myEvent.start_date.set(datetime.datetime.now())
myEvent.allday_event.set(1)
myEvent.summary.set("Test Python event!")

# newcal=myical.make(new=k.calendar)

#for anEvent in sga.events.get():
#    print "Start: ", anEvent.start_date.get()
#    print "Stop: ", anEvent.end_date.get()
#    print "AllDay: ", anEvent.allday_event.get()
#    print "UID: ", anEvent.uid.get()
#    print "Summary: ", anEvent.summary.get()
#    print "Description: ", anEvent.description.get()
#    print "- - - - - - - - - - - - - "


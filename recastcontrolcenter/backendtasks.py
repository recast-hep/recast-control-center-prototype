from celery import shared_task
import recastapi.request
import os
import sys

@shared_task
def upload_in_background(requestuuid,username,description,nevents,xsec,zipfilename):
  print 'uploading in background with\n{}\n{}\n{}\n{}\n{}\n{}'.format(requestuuid,username,description,nevents,xsec,zipfilename)
  print 'process id:', os.getpid()
  try:
      r = recastapi.request.add_parameter_point(requestuuid,username,description,nevents,xsec,zipfilename)

  except:
    print "Unexpected error:", sys.exc_info()[0]
    raise
  print "upload status: {}".format(r.ok)  


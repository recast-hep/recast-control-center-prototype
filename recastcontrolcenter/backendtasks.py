from celery import shared_task
import recastapi.request
import os
import sys
import json
import requests
import logging
log = logging.getLogger(__name__)

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

ACCESS_TOKEN = os.environ['ZENODO_TOKEN']

def createdeposition(requestuuid):
  log.info('hello')


  url = "http://sandbox.zenodo.org/api/deposit/depositions/?access_token={}".format(ACCESS_TOKEN)
  
  headers = {"Content-Type": "application/json"}
  data = {"metadata":
    {
     "access_right":"embargoed",
     "embargo_date":"2016-01-01",
     "title": "recast request response {}".format(requestuuid),
     "description":"response to a RECAST request",
     "upload_type": "dataset",
     "creators":[{"name": "Heinrich, Lukas", "affiliation": "NYU"}]
    }
   }


  r = requests.post(url, data=json.dumps(data), headers=headers)
  log.info('response: {} {}'.format(r.status_code,r.reason))
  log.info('content:{}'.format(r.content))


  deposition_id = r.json()['id']
  log.info('deposition id is: {}'.format(deposition_id))

  return deposition_id

def publish(deposition_id):
  url = "http://sandbox.zenodo.org/api/deposit/depositions/{}/actions/publish?access_token={}".format(deposition_id,ACCESS_TOKEN)
  r = requests.post(url)
  
def upload(deposition_id,filename,file):
  
  url = "http://sandbox.zenodo.org/api/deposit/depositions/{}/files?access_token={}".format(deposition_id,ACCESS_TOKEN)
  data = {'filename': filename}
  files = {'file': file}
  r = requests.post(url, data=data, files=files)
  
@shared_task
def uploadallzenodo(rootdir,requestuuid):
  depoid = createdeposition(requestuuid)


  absroot = os.path.abspath(rootdir)
  all_files = [root.rstrip('/')+'/'+f for root,subdir,files in os.walk(absroot) for f in files]
  for file in all_files:
    truncated =  file.replace('{}/'.format(absroot),'')
    upload(depoid,truncated,open(file,'rb'))

  publish(depoid)

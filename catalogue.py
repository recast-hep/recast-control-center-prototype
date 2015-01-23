import recastdmhiggs.dmhiggs_backendtasks as dmhiggs_backendtasks
import recastdmhiggs.dmhiggs_blueprint as dmhiggs_blueprint
import recasthype.hype_backendtasks as hype_backendtasks
import recasthype.hype_blueprint as hype_blueprint

implemented_analyses = {
  dmhiggs_blueprint.RECAST_ANALYSIS_ID :
      {
       'workflow':dmhiggs_backendtasks,
       'blueprint':dmhiggs_blueprint.blueprint
       },
  hype_blueprint.RECAST_ANALYSIS_ID :
      {
       'workflow':hype_backendtasks,
       'blueprint':hype_blueprint.blueprint
      }
}

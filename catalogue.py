import dmhiggs_analysis.dmhiggs_backendtasks
import dmhiggs_analysis.dmhiggs_blueprint
import hype_analysis.hype_backendtasks
import hype_analysis.hype_blueprint

implemented_analyses = {
  dmhiggs_analysis.dmhiggs_blueprint.RECAST_ANALYSIS_ID : 
      {
       'workflow':dmhiggs_analysis.dmhiggs_backendtasks,
       'blueprint': dmhiggs_analysis.dmhiggs_blueprint.blueprint
       },
  hype_analysis.hype_blueprint.RECAST_ANALYSIS_ID : 
      {
       'workflow':hype_analysis.hype_backendtasks,
       'blueprint':hype_analysis.hype_blueprint.blueprint
      }
}

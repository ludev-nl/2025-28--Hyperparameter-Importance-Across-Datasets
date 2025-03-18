from openmlfetcher import OpenMLFetcher
from fanovaservice import FanovaService
from visualiser import Visualiser

flow_id = 6969
suite_id = 99
min_runs = 200
max_runs = 500

# The task loop is not inside the class methods,
# because we will probably download one task,
# send an update to the site, and continue with the next
omlf = OpenMLFetcher(flow_id, suite_id)
tasks = omlf.fetch_tasks()
for task in tasks:
    omlf.fetch_runs(task, max_runs)
omlf.export_csv()

fnvs = FanovaService(omlf.results)
fnvs.run_fanova(min_runs)
fnvs.export_csv(flow_id, suite_id)

vis = Visualiser(fnvs.results)
vis.violinplot(show=True)
vis.crit_diff_diagram(show=True)

import openmlfetcher as omlf
import fanovaservice as fnvs
import visualiser as vis

flow_id = 6969
suite_id = 99
min_runs = 100
max_runs = 200

# The task loop is not inside the functions,
# because we will probably download one task,
# send an update to the site, and continue with the next
tasks = omlf.fetch_tasks(suite_id)
data = {}
for task in tasks[:20]:
    data[task] = omlf.fetch_runs(flow_id, task, max_runs)

# All these steps have to be executed in this order, and
# only the filtering might happen multiple times
cfg_space = fnvs.auto_configspace(data)
# Have the user edit the cfg_space as often as they want,
# and filter every time with new cfg_space
filtered_data = fnvs.filter_data(data, cfg_space)

# Finally we prepare to run fanova
imputed_data, extended_cfg_space = fnvs.impute_data(filtered_data, cfg_space)
processed_data = fnvs.prepare_data(imputed_data, extended_cfg_space)
results = fnvs.run_fanova(processed_data, extended_cfg_space, min_runs)

vis.violinplot(results, show=True)
vis.crit_diff_diagram(results, show=True)

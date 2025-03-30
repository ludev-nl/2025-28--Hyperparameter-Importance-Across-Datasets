import openmlfetcher as omlf
import fanovaservice as fnvs
import visualiser as vis

# These are the experiment settings. When testing code, consider
# setting min_runs and max_runs to 50 and 100 for example, so
# the fetching does not take too long. Also consider only taking
# the first ten tasks or so in line 19 (using '... in tasks[:10]')
flow_id = 6969
suite_id = 99
min_runs = 100
max_runs = None

# --------------------------- OpenML -----------------------------

# The task loop is not inside the functions,
# because we will probably download one task,
# send an update to the site, and continue with the next
tasks = omlf.fetch_tasks(suite_id)
data = {}
for task in tasks:
    task_data = omlf.fetch_runs(flow_id, task, max_runs)
    if task_data is None:
        print(f'Task {task}: 0')
        continue
    data[task] = omlf.coerce_types(task_data)
    print(f'Task {task}: {len(task_data)}')
# In Dash, we can't use this function: it is here so you
# can inspect the data. You could also run using
#   python -i demo.py
# so you can inspect all runtime variables in interactive mode.
omlf.export_csv(flow_id, suite_id, data)

# ------------------------- ConfigSpace -------------------------

# All these steps have }to be executed in this order, and
# only the filtering might happen multiple times
cfg_space = fnvs.auto_configspace(data)
# Have the user edit the cfg_space as often as they want,
# and filter every time with new cfg_space
filtered_data = fnvs.filter_data(data, cfg_space)

# ---------------------------- fANOVA ---------------------------

# Finally we prepare to run fanova
imputed_data, extended_cfg_space = fnvs.impute_data(filtered_data, cfg_space)
processed_data = fnvs.prepare_data(imputed_data, extended_cfg_space)
results = fnvs.run_fanova(processed_data, extended_cfg_space, min_runs)
# In Dash, we can't use this function: it is here so you
# can inspect the results.
fnvs.export_csv(flow_id, suite_id, results)

# -------------------------- Visualiser -------------------------

vis.violinplot(results, show=True)
vis.crit_diff_diagram(results, show=True)

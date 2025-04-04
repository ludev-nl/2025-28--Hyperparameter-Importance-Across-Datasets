import time

import pandas as pd

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
print('Fetching OpenML...')
section_start = time.time()

# The task loop is not inside the functions,
# because we will probably download one task,
# send an update to the site, and continue with the next
tasks = omlf.fetch_tasks(suite_id)
data = {}
end = time.time()
for task in tasks:
    start = end
    task_data = omlf.fetch_runs(flow_id, task, max_runs)
    end = time.time()
    if task_data is None:
        print(f'\tTask {task}: 0 runs, {end-start} sec')
        continue
    data[task] = omlf.coerce_types(task_data)
    print(f'\tTask {task}: {len(task_data)} runs, {end-start} sec')
# In Dash, we can't use this function: it is here so you
# can inspect the data. You could also run using
#   python -i demo.py
# so you can inspect all runtime variables in interactive mode.
omlf.export_csv(flow_id, suite_id, data)

section_end = time.time()
print(f'OpenML fetched in {section_end-section_start} sec')

# ------------------------- ConfigSpace -------------------------
print('Determining ConfigSpace...')
section_start = section_end

# All these steps have }to be executed in this order, and
# only the filtering might happen multiple times
auto_cfg_space = fnvs.auto_configspace(data)
# Have the user edit the cfg_space as often as they want,
# and filter every time with new cfg_space. The filter
# space does not have to contain every parameter, if one
# is missing, all values are accepted for it.
filter_space = auto_cfg_space  # Should let the user edit it instead
filtered_data = fnvs.filter_data(data, filter_space)
# Filtering might make parameters constant etc, so we recreate the space
cfg_space = fnvs.auto_configspace(filtered_data)

section_end = time.time()
print(f'ConfigSpace determined in {section_end-section_start} sec')

# ---------------------------- fANOVA ---------------------------
print('Running fANOVA...')
section_start = section_end

# Finally we prepare to run fanova
imputed_data, extended_cfg_space = fnvs.impute_data(filtered_data, cfg_space)
processed_data = fnvs.prepare_data(imputed_data, extended_cfg_space)
# Running fanova takes quite long, so I split it per task
results = {}
end = time.time()
for task, task_data in processed_data.items():
    start = end
    result = fnvs.run_fanova(task_data, extended_cfg_space, min_runs)
    end = time.time()
    if result:
        results[task] = result
        print(f'\tTask {task}: {end-start} sec')
results = pd.DataFrame.from_dict(results, orient='index')
# In Dash, we can't use this function: it is here so you
# can inspect the results.
fnvs.export_csv(flow_id, suite_id, results)

section_end = time.time()
print(f'fANOVA ran in {section_end-section_start} sec')

# -------------------------- Visualiser -------------------------
vis.violinplot(results, show=True)
vis.crit_diff_diagram(results, show=True)

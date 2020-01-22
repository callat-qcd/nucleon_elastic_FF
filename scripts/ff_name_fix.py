import sys

from django.db.models import Value
from django.db.models.functions import Replace
import lattedb.project.formfac.models as models
import pandas as pd
pd.set_option('display.max_colwidth', -1)

lattedb = models.TSlicedSAveragedFormFactor4DFile

ens,s   = sys.argv[1].split('_')
src_set = sys.argv[2]

db_entries = lattedb.objects.filter(
    ensemble      = ens,
    stream        = s,
    source_set    = src_set,
    #configuration = 78
    )

db_entries.update(name=Replace('name',Value('Nsnk8_src_avg'+src_set),Value('Srcs'+src_set+'_src_avg')))

print(db_entries.to_dataframe(fieldnames=['ensemble','stream','configuration','source_set','t_separation','name']))

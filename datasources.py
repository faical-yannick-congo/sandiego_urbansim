import os
import numpy as np
import pandas as pd

import orca
from urbansim.utils import misc
from urbansim_defaults import datasources

@orca.table('jobs', cache=True)
def jobs(store):
    df = store['jobs']
    df = df[df.building_id > 0]
    return df
    
@orca.table('travel_data', cache=True)
def travel_data(store):
    df = store['travel_data']
    return df
    
@orca.table('zones', cache=True)
def zones(travel_data):
    df = pd.DataFrame(index = np.unique(travel_data.to_frame().reset_index().from_zone_id))
    return df
    
@orca.table('fee_schedule', cache=True)
def fee_schedule(store):
    df = store['fee_schedule']
    return df
    
@orca.table('parcel_fee_schedule', cache=True)
def parcel_fee_schedule(store):
    df = store['parcel_fee_schedule']
    return df
    
@orca.table('zoning', cache=True)
def zoning(store):
    df = store['zoning']
    return df
    
@orca.table('scheduled_development_events', cache=True)
def scheduled_development_events(store):
    df = store['scheduled_development_events']
    return df
    
@orca.table('zoning_allowed_uses', cache=True)
def zoning_allowed_uses(store, parcels):
    parcels_allowed = store['zoning_allowed_uses']
    parcels = orca.get_table('parcels').to_frame(columns = ['zoning_id',])
    
    allowed_df = pd.DataFrame(index = parcels.index)
    for devtype in np.unique(parcels_allowed.development_type_id):
        devtype_allowed = parcels_allowed[parcels_allowed.development_type_id == devtype].set_index('zoning_id')
        allowed = misc.reindex(devtype_allowed.development_type_id, parcels.zoning_id)
        df = pd.DataFrame(index=allowed.index)
        df['allowed'] = False
        df[~allowed.isnull()] = True
        allowed_df[devtype] = df.allowed

    return allowed_df
    
@orca.table('households', cache=True)
def households(store):
    df = store['households']
    df = df[df.building_id > 0]  ##Revisit the allocation and remove GQ from synthetic population?
    
    p = store['parcels']
    b = store['buildings']
    b['luz'] = misc.reindex(p.luz_id, b.parcel_id)
    df['base_luz'] = misc.reindex(b.luz, df.building_id)
    df['segmentation_col'] = 1
    
    return df
    
@orca.table('buildings', cache=True)
def buildings(store):
    df = store['buildings']
    df['res_price_per_sqft'] = 0.0
    df['nonres_rent_per_sqft'] = 0.0
    #df.residential_units = df.residential_units*2  ##For testing HLCM luz supply constraints only
    return df
    
@orca.table('parcels', cache=True)
def parcels(store):
    df = store['parcels']
    df['acres'] = df.parcel_acres
    
    #Delete duplicate index (parcel_id)
    df['rownum'] = df.index
    df = df.drop_duplicates(cols='rownum', take_last=True)
    del df['rownum']
    
    return df
    
@orca.table('annual_household_control_totals', cache=True)
def annual_household_control_totals(store):
    hh_controls = store['hh_controls']
    return hh_controls
    
@orca.injectable('building_sqft_per_job', cache=True)
def building_sqft_per_job(settings):
    return settings['building_sqft_per_job']
    
# non-residential rent data
@orca.table('costar', cache=True)
def costar(store):
    df = store['costar']
    return df
    
# residential price data
@orca.table('assessor_transactions', cache=True)
def assessor_transactions(store):
    df = store['assessor_transactions']
    df["index"] = df.index
    df.drop_duplicates(cols='index', take_last=True, inplace=True)
    del df["index"]
    return df
    
@orca.table('luz_base_indicators', cache=True)
def luz_base_indicators(store):
    households = store['households'][['building_id']]
    jobs = store['jobs'][['building_id']]
    buildings = store['buildings'][['parcel_id']]
    parcels = store['parcels'][['luz_id']]
    buildings['luz_id'] = misc.reindex(parcels.luz_id, buildings.parcel_id)
    households['luz_id'] = misc.reindex(buildings.luz_id, households.building_id)
    jobs['luz_id'] = misc.reindex(buildings.luz_id, jobs.building_id)
    hh_luz_base = households.groupby('luz_id').size()
    emp_luz_base = jobs.groupby('luz_id').size()
    return pd.DataFrame({'hh_base':hh_luz_base, 'emp_base':emp_luz_base})


# this specifies the relationships between tables
orca.broadcast('nodes', 'costar', cast_index=True, onto_on='node_id')
orca.broadcast('parcels', 'costar', cast_index=True, onto_on='parcel_id')
orca.broadcast('nodes', 'assessor_transactions', cast_index=True, onto_on='node_id')
orca.broadcast('parcels', 'assessor_transactions', cast_index=True, onto_on='parcel_id')
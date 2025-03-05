
-- get in the data_dispatcher schema.

set search_path = data_dispatcher;

-- in 2.0 we will need the "urls" column (as well as "url") in 
-- the replicas table and the replicas_with_rse_availability view.

alter table replicas add column urls jsonb default '[]'::jsonb;

drop view if exists replicas_with_rse_availability;
create view replicas_with_rse_availability as
    select replicas.*, rses.is_available as rse_available
        from replicas, rses
        where rses.name = replicas.rse and rses.is_enabled
;
grant select, insert, update, delete, truncate, references, trigger on replicas_with_rse_availability to dm_admin;

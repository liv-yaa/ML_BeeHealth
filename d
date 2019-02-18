                                             Table "public.bees"
     Column      |            Type             | Collation | Nullable |               Default                
-----------------+-----------------------------+-----------+----------+--------------------------------------
 bee_id          | integer                     |           | not null | nextval('bees_bee_id_seq'::regclass)
 health          | character varying(1)        |           |          | 
 datetime        | timestamp without time zone |           |          | 
 filename        | character varying(100)      |           |          | 
 location        | character varying(30)       |           |          | 
 zip_code        | character varying(10)       |           |          | 
 subspecies      | character varying(30)       |           |          | 
 pollen_carrying | character varying(10)       |           |          | 
 caste           | character varying(10)       |           |          | 
Indexes:
    "bees_pkey" PRIMARY KEY, btree (bee_id)
Referenced by:
    TABLE "photos" CONSTRAINT "photos_bee_id_fkey" FOREIGN KEY (bee_id) REFERENCES bees(bee_id)


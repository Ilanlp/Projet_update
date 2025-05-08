USE DATABASE JOB_MARKET;
USE SCHEMA PUBLIC;

CREATE OR REPLACE FILE FORMAT classic_csv type='csv' compression='auto' field_delimiter=',' record_delimiter='\n' skip_header=1 field_optionally_enclosed_by='\"' trim_space=false error_on_column_count_mismatch=true escape='NONE' escape_unenclosed_field='\134' date_format='auto' timestamp_format='auto' null_if=('\\N');

CREATE OR REPLACE FILE FORMAT csv_error type='csv' compression='auto' field_delimiter=',' record_delimiter='\n' skip_header=1 field_optionally_enclosed_by='\"' trim_space=false error_on_column_count_mismatch=false escape='NONE' escape_unenclosed_field='\134' date_format='auto ' timestamp_format='auto' null_if=('','\\N');
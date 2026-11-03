-- Development-only seed: ~20 well-known NSE symbols so the instrument master
-- has real data to validate holdings against and to search over. This is
-- NOT a complete NSE/BSE listing - see docs/known-limitations.md. A future
-- ingestion job (e.g. from an NSE/BSE bhavcopy or equivalent) will insert
-- real rows with data_source = 'nse_bhavcopy_import' (or similar) alongside
-- or instead of these; no schema change is required for that.
--
-- Run this after 0001_init.sql, in the Supabase SQL editor.

insert into public.instruments (exchange, symbol, company_name, data_source) values
    ('NSE', 'RELIANCE',   'Reliance Industries Ltd',              'dev_seed'),
    ('NSE', 'TCS',        'Tata Consultancy Services Ltd',        'dev_seed'),
    ('NSE', 'INFY',       'Infosys Ltd',                          'dev_seed'),
    ('NSE', 'HDFCBANK',   'HDFC Bank Ltd',                        'dev_seed'),
    ('NSE', 'ICICIBANK',  'ICICI Bank Ltd',                       'dev_seed'),
    ('NSE', 'SBIN',       'State Bank of India',                  'dev_seed'),
    ('NSE', 'ITC',        'ITC Ltd',                              'dev_seed'),
    ('NSE', 'LT',         'Larsen & Toubro Ltd',                  'dev_seed'),
    ('NSE', 'HINDUNILVR', 'Hindustan Unilever Ltd',               'dev_seed'),
    ('NSE', 'BHARTIARTL', 'Bharti Airtel Ltd',                    'dev_seed'),
    ('NSE', 'KOTAKBANK',  'Kotak Mahindra Bank Ltd',              'dev_seed'),
    ('NSE', 'AXISBANK',   'Axis Bank Ltd',                        'dev_seed'),
    ('NSE', 'ASIANPAINT', 'Asian Paints Ltd',                     'dev_seed'),
    ('NSE', 'MARUTI',     'Maruti Suzuki India Ltd',              'dev_seed'),
    ('NSE', 'SUNPHARMA',  'Sun Pharmaceutical Industries Ltd',    'dev_seed'),
    ('NSE', 'TITAN',      'Titan Company Ltd',                    'dev_seed'),
    ('NSE', 'WIPRO',      'Wipro Ltd',                             'dev_seed'),
    ('NSE', 'ULTRACEMCO', 'UltraTech Cement Ltd',                 'dev_seed'),
    ('NSE', 'BAJFINANCE', 'Bajaj Finance Ltd',                    'dev_seed'),
    ('NSE', 'NESTLEIND',  'Nestle India Ltd',                     'dev_seed')
on conflict (exchange, symbol) do nothing;

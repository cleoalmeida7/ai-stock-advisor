-- Development-only seed: ~20 well-known NSE symbols so the instrument master
-- has real data to validate holdings against and to search over. This is
-- NOT a complete NSE/BSE listing - see docs/known-limitations.md. A future
-- ingestion job (e.g. from an NSE/BSE bhavcopy or equivalent) will insert
-- real rows with data_source = 'nse_bhavcopy_import' (or similar) alongside
-- or instead of these; no schema change is required for that.
--
-- sector is an approximate, development-purpose primary-sector
-- classification (simplified GICS-like taxonomy) - not a licensed
-- sector-data feed. See docs/known-limitations.md.
--
-- Run this after 0001_init.sql and 0002_price_history.sql, in the Supabase
-- SQL editor. Safe to re-run: inserts are skipped if the row already
-- exists, and the sector UPDATEs are idempotent (they just set the same
-- value again).

insert into public.instruments (exchange, symbol, company_name, data_source, sector) values
    ('NSE', 'RELIANCE',   'Reliance Industries Ltd',           'dev_seed', 'Energy'),
    ('NSE', 'TCS',        'Tata Consultancy Services Ltd',     'dev_seed', 'Information Technology'),
    ('NSE', 'INFY',       'Infosys Ltd',                       'dev_seed', 'Information Technology'),
    ('NSE', 'HDFCBANK',   'HDFC Bank Ltd',                     'dev_seed', 'Financial Services'),
    ('NSE', 'ICICIBANK',  'ICICI Bank Ltd',                    'dev_seed', 'Financial Services'),
    ('NSE', 'SBIN',       'State Bank of India',               'dev_seed', 'Financial Services'),
    ('NSE', 'ITC',        'ITC Ltd',                           'dev_seed', 'Consumer Staples'),
    ('NSE', 'LT',         'Larsen & Toubro Ltd',               'dev_seed', 'Industrials'),
    ('NSE', 'HINDUNILVR', 'Hindustan Unilever Ltd',            'dev_seed', 'Consumer Staples'),
    ('NSE', 'BHARTIARTL', 'Bharti Airtel Ltd',                 'dev_seed', 'Telecommunication Services'),
    ('NSE', 'KOTAKBANK',  'Kotak Mahindra Bank Ltd',           'dev_seed', 'Financial Services'),
    ('NSE', 'AXISBANK',   'Axis Bank Ltd',                     'dev_seed', 'Financial Services'),
    ('NSE', 'ASIANPAINT', 'Asian Paints Ltd',                  'dev_seed', 'Materials'),
    ('NSE', 'MARUTI',     'Maruti Suzuki India Ltd',           'dev_seed', 'Consumer Discretionary'),
    ('NSE', 'SUNPHARMA',  'Sun Pharmaceutical Industries Ltd', 'dev_seed', 'Health Care'),
    ('NSE', 'TITAN',      'Titan Company Ltd',                 'dev_seed', 'Consumer Discretionary'),
    ('NSE', 'WIPRO',      'Wipro Ltd',                         'dev_seed', 'Information Technology'),
    ('NSE', 'ULTRACEMCO', 'UltraTech Cement Ltd',              'dev_seed', 'Materials'),
    ('NSE', 'BAJFINANCE', 'Bajaj Finance Ltd',                 'dev_seed', 'Financial Services'),
    ('NSE', 'NESTLEIND',  'Nestle India Ltd',                  'dev_seed', 'Consumer Staples')
on conflict (exchange, symbol) do nothing;

update public.instruments set sector = 'Energy' where exchange = 'NSE' and symbol = 'RELIANCE' and sector is null;
update public.instruments set sector = 'Information Technology' where exchange = 'NSE' and symbol = 'TCS' and sector is null;
update public.instruments set sector = 'Information Technology' where exchange = 'NSE' and symbol = 'INFY' and sector is null;
update public.instruments set sector = 'Financial Services' where exchange = 'NSE' and symbol = 'HDFCBANK' and sector is null;
update public.instruments set sector = 'Financial Services' where exchange = 'NSE' and symbol = 'ICICIBANK' and sector is null;
update public.instruments set sector = 'Financial Services' where exchange = 'NSE' and symbol = 'SBIN' and sector is null;
update public.instruments set sector = 'Consumer Staples' where exchange = 'NSE' and symbol = 'ITC' and sector is null;
update public.instruments set sector = 'Industrials' where exchange = 'NSE' and symbol = 'LT' and sector is null;
update public.instruments set sector = 'Consumer Staples' where exchange = 'NSE' and symbol = 'HINDUNILVR' and sector is null;
update public.instruments set sector = 'Telecommunication Services' where exchange = 'NSE' and symbol = 'BHARTIARTL' and sector is null;
update public.instruments set sector = 'Financial Services' where exchange = 'NSE' and symbol = 'KOTAKBANK' and sector is null;
update public.instruments set sector = 'Financial Services' where exchange = 'NSE' and symbol = 'AXISBANK' and sector is null;
update public.instruments set sector = 'Materials' where exchange = 'NSE' and symbol = 'ASIANPAINT' and sector is null;
update public.instruments set sector = 'Consumer Discretionary' where exchange = 'NSE' and symbol = 'MARUTI' and sector is null;
update public.instruments set sector = 'Health Care' where exchange = 'NSE' and symbol = 'SUNPHARMA' and sector is null;
update public.instruments set sector = 'Consumer Discretionary' where exchange = 'NSE' and symbol = 'TITAN' and sector is null;
update public.instruments set sector = 'Information Technology' where exchange = 'NSE' and symbol = 'WIPRO' and sector is null;
update public.instruments set sector = 'Materials' where exchange = 'NSE' and symbol = 'ULTRACEMCO' and sector is null;
update public.instruments set sector = 'Financial Services' where exchange = 'NSE' and symbol = 'BAJFINANCE' and sector is null;
update public.instruments set sector = 'Consumer Staples' where exchange = 'NSE' and symbol = 'NESTLEIND' and sector is null;
